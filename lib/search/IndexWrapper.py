
from django.conf import settings
from .constants import MELODIC_SEARCH, RHYTHMIC_SEARCH,DIATONIC_SEARCH,EXACT_SEARCH

import os

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index
from elasticsearch_dsl import Document, Integer, Text, Object, Nested, InnerDoc
from elasticsearch_dsl import Q
from elasticsearch.helpers import bulk

import json
from operator import itemgetter

from manager.models import Corpus, Opus, OpusMeta
from music import *
from search.Sequence import Sequence
from search.MusicSummary import MusicSummary

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Debug level for HTTP requests
logging.getLogger("urllib3").setLevel(logging.WARNING)

class IndexWrapper:
	"""
	
	A class to send NEUMA-specific queries to ElasticSearch
	
	This class acts as a proxy for all queries sent to ElasticSearch. It relies on
	the ``elasticsearch_dsl`` package, documented here:
	https://elasticsearch-dsl.readthedocs.io/en/latest/. 
	
	"""

	def __init__(self, auth_login=None, auth_password=None) :
		"""
		   Connect to the ElasticSearch server, and open the index
		"""
		if auth_login is None:
			self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"], 
											port=settings.ELASTIC_SEARCH["port"],
											index=settings.ELASTIC_SEARCH["index"])
		else:
			self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"], 
											port=settings.ELASTIC_SEARCH["port"],
											index=settings.ELASTIC_SEARCH["index"],
											http_auth=(auth_login, auth_password))
			
		es_logger = logging.getLogger('elasticsearch')
		es_logger.setLevel(logging.WARNING)
		
		# Open, and possibly create the index
		self.index = Index (settings.ELASTIC_SEARCH["index"],using=self.elastic_search)
		
		if not self.index.exists(using=self.elastic_search):
			# Create the index
			self.index.create(using=self.elastic_search)
			self.index.settings(number_of_shards=1, number_of_replicas=0)

		self.index.open(using=self.elastic_search)
		#: Directory containing some pre-defined queries in JSON
		self.query_dir = settings.ES_QUERY_DIR
		
	
	def get_index_info (self):
		'''
		Obtain main infos on the index
		'''
		return self.index.get()

	def index_opus (self, opus):
		""" 
		Add of replace an Opus in the ElasticSeaerch index
		
		"""
		
		print ("Index Opus " + opus.ref)
		# First time that we index this Opus
		try:
			score = opus.get_score()

			# New change: store MS in ES
			music_summary = score.get_music_summary()
			music_summary.opus_id = opus.ref
			msummary_for_es = music_summary.encode()

			opus_index = OpusIndex(
				meta={'id': opus.ref, 'index': settings.ELASTIC_SEARCH["index"]},
				corpus_ref=opus.corpus.ref,
				ref=opus.ref,
				summary = msummary_for_es,
				title=opus.title,
				composer=opus.composer,
				lyricist=opus.lyricist,
			)
			
			# Add features if any
			for meta in opus.get_metas ():
				if meta.meta_key == OpusMeta.MK_KEY_TONIC:
					opus_index.key = meta.meta_value
				if meta.meta_key == OpusMeta.MK_KEY_MODE:
					opus_index.mode = meta.meta_value
				if meta.meta_key == OpusMeta.MK_NUM_OF_PARTS:
					opus_index.nb_of_parts = meta.meta_value
				
			# Add descriptors to opus index
			for descriptor in opus.descriptor_set.all():
				#print ("Add descriptor for voice " + descriptor.voice, " type " + descriptor.type)
				opus_index.add_descriptor(descriptor)
			# Saving the opus_index object triggers insert or replacement in ElasticSearch
			opus_index.save(using=self.elastic_search,id=opus.ref)

		except Exception as ex:
			print ("Error met when trying to index: " + str(ex))
			#When the analysis finish, no value would be assigned to mel_pat_dict etc.. thus simply return void
		
		return


		# Add descriptors to opus index
		for descriptor in opus.descriptor_set.all():
			#print ("Add descriptor for voice " + descriptor.voice, " type " + descriptor.type)
			opus_index.add_descriptor(descriptor)

		# Saving the opus_index object triggers insert or replacement in ElasticSearch
		opus_index.save(using=self.elastic_search,id=opus.ref)

	def get_all_corpora(self):
		"""
		 Get the list of all corpora 
		 
		 The query is encoded in a Json file, loaded and executed. It returns the
		 list of corpora
		 
		"""
		with open(self.query_dir + '/' + 'all_corpora_search.json', 'r') as query_file:
			query = json.loads(query_file.read())
		
		res = self.elastic_search.search(index=settings.ELASTIC_SEARCH["index"], 
										 doc_type ="Corpus", body=query)
		corpora = []
		for hit in res['hits']['hits']:
			corpora.append(hit["_source"])

		return corpora

	def ranked_search(self, search_context):
		"""
		Run a search with internal ES ranking
		"""
		
		# Create the standard search object
		std_query = self.get_search(search_context)
		 
		# Create the ranked search object
		search = Search(using=self.elastic_search)
		
		with open(self.query_dir + '/' + 'ranked_search.json', 'r') as query_file:
			query = json.loads(query_file.read())
 
		query['query']['function_score']['functions'][0]['script_score']['script']['params']['query'] = search_context.get_pattern_sequence().encode()
		 
		# Set the correct query part of the ranked search
		query['query']['function_score']['query'] = std_query.to_dict()['query']

		#query['query']['function_score']
		print ("Ranked search query " + str(query).replace("\"", "\\\"").replace("'", "\""))
			   
		search.from_dict(query)
		return search

	def search(self, search_context):
		'''
		Search function: sends a combined query to ElasticSearch
		'''

		# print ("Search with keyword '" + search_context.keywords)
		# members = inspect.getmembers(search_context)
		# for member in members:
		#	print ("Member " + str(member))

		if search_context.keywords == "Keywords":
			# Sometimes the default text is sent as such
			search_context.keywords = ''

		pattern_sequence = search_context.get_pattern_sequence()
		print("Search with corpus '" + search_context.ref 
			   + "'  Keywords: '" + search_context.keywords + "'"
			   + "'  Pattern: [" + str(pattern_sequence) + "]")
		
		# Get search query
		if settings.ES_RANKED_SEARCH:
			# We use our own internal ranked search
			search = self.ranked_search(search_context)
		else:
			search = self.get_search(search_context)
			 
		logger.info ("Search doc sent to ElasticSearch: " + str(search.to_dict()))
		print ("Search doc sent to ElasticSearch: " + str(search.to_dict()).replace("'", "\""))
		# Get results
		results = search.execute()

		# Create the result by decoding the opus got from ElasticSearch
		opera = []
		# Utiliser scan() au lieu de parcourir 'results' pour obtenir tous les résultats
		count_match_for_exact_search = 0
		# Philippe la boucle  "for hit in search.scan()" plante sur Humanum...
		for hit in search:
			try:
				if hit.corpus_ref == 'all:composers:liyanfei': continue
				# Nicolas rajout de ce test car des documents de mappings peuvent apparaitre dans elasticsearch 6.1.2
				if "ref" in hit:
					opus = Opus.objects.get(ref=hit["ref"])
					matching_ids = []
					distance = 0
					best_occurrence = None
					# Find the occurrences in MusicSummary, if search type is pattern search
					# Using MusicSummary to locate hits in the results returned by elasticsearch
					if search_context.is_pattern_search():
						msummary = MusicSummary()
						if opus.summary:
							with open(opus.summary.path, "r") as summary_file:
								msummary_content = summary_file.read()
							msummary.decode(msummary_content)

							pattern_sequence = search_context.get_pattern_sequence()

							#No mirror search mode for exact search
							if search_context.search_type == EXACT_SEARCH:
								mirror_setting = False
								count_match_for_exact_search+=1
								occurrences = msummary.find_exact_matches(pattern_sequence, search_context.search_type)

							if search_context.search_type == MELODIC_SEARCH or search_context.search_type == DIATONIC_SEARCH or search_context.search_type == RHYTHMIC_SEARCH:
								#return the sequences that match and the distances
								mirror_setting = search_context.is_mirror_search()

								# Find the occurrences of matches within the opus, 
								# and measure the melodic or rhythmic distance depending on context
								# If there is more than one match in an opus,
								# we only take the distance between the best match(with least distance with the query)
								# The "best_occurrence" here should be a pattern sequence.
								best_occurrence, distance = msummary.get_best_occurrence(pattern_sequence, search_context.search_type, mirror_setting)
								logger.info ("Found best occurrence : " + str(best_occurrence) + " with distance " + str(distance))

							#Find matching ids for the matches to highlight
							matching_ids = msummary.find_matching_ids(pattern_sequence, search_context.search_type, mirror_setting)
						else:
							logger.warning("No summary for Opus " + opus.ref)
					#If search by keywords
					elif search_context.is_keyword_search():

						'''
							Instead of getting MusicSummary and locate the pattern when the search type is pattern search, 
							here we directly get scores from the opus that match in the search,
							and find if the keyword is in the lyrics of the opus.
						'''
						best_occurrence = ""
						#always "" in keyword search mode because it is supposed to be a pattern sequence
						distance = 0
						#No distance measurement for keyword search
						matching_ids = []
						#IDs of matching M21 objects
						print("#######################################")
						score = opus.get_score()
						#Find the matching id by locating keywords in the score
						for voice in score.get_all_voices():
							#get lyrics of the current voice
							curr_lyrics = voice.get_lyrics()
							if curr_lyrics != None:
								if search_context.keywords in curr_lyrics:
									#There is a match within the current lyrics
									occurrences, curr_matching_ids = voice.search_in_lyrics(search_context.keywords)
									if occurrences > 0:
										#If there is a match
										print("Found occurrence in opus_id:  ", opus.id)
										print("Appeared in voice: ", voice.id, ", occurrences: ", occurrences)
										for m_id in curr_matching_ids:
											matching_ids.append(m_id)
					opera.append({"opus": opus, "matching_ids": json.dumps(matching_ids), "distance": distance, "best_occurrence": str(best_occurrence)})
			except Opus.DoesNotExist:
				logger.warning ("Opus " +  hit["_id"] + " found in ES but not in the DB")
		
		# Sort results by score
		if settings.ES_RANKED_SEARCH:
			#print("Ranked within elasticsearch!")
			#If search type is melodic/rhythmic, so the rhythmic/melodic distance is calculatable
			if search_context.search_type == MELODIC_SEARCH or search_context.search_type == RHYTHMIC_SEARCH or search_context.search_type == DIATONIC_SEARCH:
				opera = sorted(opera, key=itemgetter('distance'))
				for o in opera:
					print(str(o["best_occurrence"]) + " : " + str(o["distance"]))
		
		return opera

	def export_all(self, output_dir):
		es = Elasticsearch()
		
		resp = es.search(index=settings.ELASTIC_SEARCH["index"], 
						 scroll="10m", 
						 size= 100,
						 query={"match_all": {}})
		scroll_id = resp['_scroll_id']
		scroll_size = len(resp['hits']['hits'])
		
		print("Scroll id %s and scroll size %s " % (str(scroll_id), str(scroll_size)))
		i_doc = 0
		while scroll_size > 0:
			print ("Scrolling...")
			for hit in resp['hits']['hits']:
				id = hit['_id'].replace(':', '_').replace('.','_')
				file_path = os.path.join(output_dir, id +'.json')
				print ("File : " + file_path)
				with open(file_path, 'w', encoding='utf-8') as f:
					json.dump(hit["_source"], f)
				i_doc+= 1
			resp  = es.scroll(scroll_id=scroll_id, scroll='2m')
			scroll_id = resp['_scroll_id']
			scroll_size = len(resp['hits']['hits'])


		print ("%d documents have been exported." % i_doc)
		return

	def get_search(self, search_context):
		"""
		Create the search object with ElasticSearch DSL
		"""
		search = Search(using=self.elastic_search)
		search = search.params (size=settings.MAX_ITEMS_IN_RESULT)
		# Do we search in a specific corpus?
		if search_context.ref and search_context.ref != "all":
			search = search.query("prefix", corpus_ref=search_context.ref)

		# Do we search for keywords?
		if search_context.keywords:
			# Searching for the keywords in titles and composers
			q_title = Q("multi_match", query=search_context.keywords, fields=['lyrics', 'composer', 'title'])
			# Searching for the keywords in lyrics
			q_lyrics = Q("match_phrase", lyrics__value=search_context.keywords)
			# Combine the search
			search = search.query(q_title | q_lyrics)

		# Do we search a melodic pattern
		if search_context.is_pattern_search():
			if search_context.search_type == RHYTHMIC_SEARCH:
				search = search.query("match_phrase", rhythm__value=search_context.get_rhythmic_pattern())

			elif search_context.search_type == MELODIC_SEARCH:
				# If mirror search mode is on, search the mirror patterns too.
				if search_context.is_mirror_search() == True:
					# calling get_melodic_pattern function returns a tuple of 2 lists here
					mel_patterns = search_context.get_melodic_pattern(True)
					og_patterns = mel_patterns[0]
					mr_patterns = mel_patterns[1]
					# Search for the original patterns
					q_og = Q("match_phrase", melody__value=og_patterns)
					# Search for the mirror patterns
					q_mr = Q("match_phrase", melody__value=mr_patterns)
					# Combine the search
					search = search.query(q_og | q_mr)
				else:
					# Otherwise only search for the original melody patterns
					search = search.query("match_phrase", melody__value=search_context.get_melodic_pattern())

			elif search_context.search_type == EXACT_SEARCH:
				search = search.query("match_phrase", notes__value=search_context.get_notes_pattern())

			elif search_context.search_type == settings.DIATONIC_SEARCH:
				# If mirror search mode is on
				if search_context.is_mirror_search() == True:
					# dia_patterns includes two lists, a list of original patterns and a list of mirror patterns
					dia_patterns = search_context.get_diatonic_pattern(True)
					# original patterns
					og_patterns = dia_patterns[0]
					# mirror patterns
					mr_patterns = dia_patterns[1]
					q_og = Q("match_phrase", diatonic__value=og_patterns)
					q_mr = Q("match_phrase", diatonic__value=mr_patterns)
					search = search.query(q_og | q_mr)
				else:
					# Otherwise only search for the original diatonic patterns
					search = search.query("match_phrase", diatonic__value=search_context.get_diatonic_pattern())

		return search
	
	def delete_index(self):
		print ("Deleting index " + settings.ELASTIC_SEARCH["index"])
		self.elastic_search.indices.delete(index=settings.ELASTIC_SEARCH["index"], ignore=[400, 404])

	def bulk_indexing():
		'''
			Index all descriptor objects into ElasticSearch
		'''
		OpusIndex.init(index=settings.ELASTIC_SEARCH["index"])
		Descriptor = apps.get_model('manager', 'descriptor')
		bulk(client=self.elas, actions=(b.indexing() for b in Descriptor.objects.all().iterator()))

class DescriptorIndex(InnerDoc):
	'''
	 Encoding of a specific descriptor for a voice, stored in ElasrticSearch
	 
	 A descriptor is a character string that encodes a specific aspect (rhythm, melody, lyrics)
	 of a voice in a music piece. Its structure (sequence of ngrams) is such that effective text-based search
	 supported by ElasticSearch can be carried out on its content.
	'''
	
	part = Text()
	voice = Text()
	value = Text()

class OpusIndex(Document):
	'''
	 Encoding of informations related to an Opus, stored in ElasrticSearch
	'''
	corpus_ref = Text()
	id = Integer()
	ref = Text()
	title = Text()
	lyricist = Text()
	composer = Text()
	
	# Features
	key = Text()
	mode = Text()
	key_and_mode = Text()
	nb_of_parts = Integer()

	# Music summary: compressed representation of the music content
	summary = Text()
	#: Ngram encoding of the melody
	melody = Nested(
		doc_class=DescriptorIndex,
	)
	#: Ngram encoding of the rythm
	rhythm = Nested(
		doc_class=DescriptorIndex,
	)
	#: Ngram encoding of the notes
	notes = Nested(
		doc_class=DescriptorIndex,
	)
	#: Text encoding of the lyrics
	lyrics = Nested(
		doc_class=DescriptorIndex,
	)
	# Ngram encoding of the diatonic intervals
	diatonic = Nested(
		doc_class=DescriptorIndex,
	)
	'''
	  Add a new descriptor to the OpusIndex. Must be done before sending the latter to ES
	'''
	def add_descriptor(self, descriptor):
		if descriptor.type == settings.LYRICS_DESCR:
			self.lyrics = self.update_list(self.lyrics, descriptor.to_dict(), 'voice')
		elif descriptor.type == settings.MELODY_DESCR:
			self.melody = self.update_list(self.melody, descriptor.to_dict(), 'voice')
		elif descriptor.type == settings.RHYTHM_DESCR:
			self.rhythm = self.update_list(self.rhythm, descriptor.to_dict(), 'voice')
		elif descriptor.type == settings.NOTES_DESCR:
			self.notes = self.update_list(self.notes, descriptor.to_dict(), 'voice')
		elif descriptor.type == settings.DIATONIC_DESCR:
			self.diatonic = self.update_list(self.diatonic, descriptor.to_dict(), 'voice')


	@staticmethod
	def update_list(l, d, attr):
		updated = False
		
		for i, item in enumerate(l):
			if item[attr] == d[attr]:
				l[i] = d
				updated = True

		if not updated:
			l.append(d)
		return l
