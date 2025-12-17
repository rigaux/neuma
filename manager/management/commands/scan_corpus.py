from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus

from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm

from workflow.Workflow import Workflow
#from dmining.models import StatsDesc
import string
import os
import re
import subprocess
from django.core.files import File
import csv

from lib.music.Score import *
from lib.music.Voice import IncompleteBarsError


from neumasearch.IndexWrapper import IndexWrapper

# List of actions

TO_MEI_ACTION = "mei"
CLEAR_INDEX_ACTION="clearindex"
INDEX_ACTION="index"
PROPAGATE_ACTION="propagate"
INDEX_ALL_ACTION = "index_all"
STATS_ACTION="stats"
TITLE_ACTION="title"
CPTDIST="cptdist"
QUALEVAL="qualeval"
FIX_PERMISSIONS_ACTION="fix_permissions"
DESCRIPTORJSON_ACTION="descriptorjson"
ANALYZE_CORPUS_ACTION = "analyze"
ANALYZE_OPUS_ACTION = "analyze_opus"
COPY_DMOS_ACTION = "copy_dmos"
EXPORT_TO_MUSICDIFF_ACTION = "export_musicdiff"
CONVERT_GALLICA = "convert_gallica"

EXTRACT_FEATURES_ACTION = "extract_features"

class Command(BaseCommand):
	"""Scan a corpus specified as input, and apply some action"""

	help = 'Scan a corpus specified as input, and apply some action'

	def add_arguments(self, parser):
		parser.add_argument('-c', dest='corpus_ref')
		parser.add_argument('-a', dest='action')
		parser.add_argument('-o', dest='opus_ref')
		parser.add_argument('-k', dest='class_number')
		parser.add_argument('-t', dest='corpus_target')
		parser.add_argument('-d', dest='descriptor')
		parser.add_argument('-m', dest='metric')

	def handle(self, *args, **options):
		action = options['action']

		# Actions that do not need corpus argument
		if action == CLEAR_INDEX_ACTION:
			index_wrapper = IndexWrapper()
			index_wrapper.delete_index()
			return 
		elif action == INDEX_ALL_ACTION:
			corpora = Corpus.objects.all()
			for c in corpora:
				if not c.parent_ref(c.ref):
					Workflow.index_corpus(c)
			return 
		elif action == EXPORT_TO_MUSICDIFF_ACTION:
			# Export the reference and computed MEI to 'ground-truth'
			# and 'predicted' dirs of the utilities 
			try:
				corpus = Corpus.objects.get(ref=options['corpus_ref'])
				Workflow.export_to_musicdiff(corpus)
			except Corpus.DoesNotExist:
				raise CommandError('Corpus "%s" does not exist' % options['corpus_ref'])
			return "Done"
		elif action == CONVERT_GALLICA:
			# Import the V3 manifest from Gallica, given the document id
			try:
				corpus = Corpus.objects.get(ref=options['corpus_ref'])
				Workflow.convert_gallica(corpus)
			except Corpus.DoesNotExist:
				raise CommandError('Corpus "%s" does not exist' % options['corpus_ref'])
			return "Done"
		elif action == PROPAGATE_ACTION:
			root_corpus = Corpus(ref=settings.NEUMA_ROOT_CORPUS_REF)
			Workflow.propagate(root_corpus)
			print ("Licences and composers propagated from top-level corpora to children")
			return 

		try:
			corpus = Corpus.objects.get(ref=options['corpus_ref'])
			opusref = options['opus_ref']
		except Corpus.DoesNotExist:
				raise CommandError('Corpus "%s" does not exist' % options['corpus_ref'])

		if not opusref: 
			if action is None:
				self.stdout.write("Please supply an action ")
				return
			self.stdout.write('Scanning corpus "%s" with action: %s' % (corpus.title,action))			

			if action == TO_MEI_ACTION:
				Workflow.produce_mei(corpus)
				print ("MEI conversion completed for " + corpus.title)
			elif action == INDEX_ACTION:
				Workflow.index_corpus(corpus)
				print ("Indexing completed for corpus '" + corpus.title + "'")
			elif action == TITLE_ACTION:		
				for opus in Opus.objects.filter(corpus__ref=corpus.ref):
					self.stdout.write("Found opus " + opus.title)
					score = opus.get_score()

					self.stdout.write("Score title " + score.get_title())
					if score.get_title() != None and len(score.get_title()) > 0:
						opus.title = score.get_title()
						opus.save()
					if score.get_composer() != None and len(score.get_composer()) > 0:
						opus.composer = score.get_composer()
						opus.save()
						
			elif action == STATS_ACTION:
				for opus in Opus.objects.filter(corpus__ref=corpus.ref):
					self.stdout.write("Found opus " + opus.title)
					if opus.musicxml:
						if os.path.isfile( opus.musicxml.path):
							musicxml = opus.musicxml.read()
							self.stdout.write("Size of MusicXML file for " + opus.title + " = " + str(len(musicxml)))
							self.stdout.write("Essai de stats")
							stats = StatsDesc(opus)
							self.stdout.write(stats.name)
						else:
							self.stdout.write("Warning: invalid MusicXML file path for " + opus.title)
					else:
						self.stdout.write("Warning: no MusicXML for opus " + opus.title)

			elif action == ANALYZE_CORPUS_ACTION:
				"""
				Analyze all patterns in corpus to get the most frequent ones
				"""
				try:
					Workflow.analyze_patterns(corpus)
					print("Done.")
				except corpus.DoesNotExist:
					raise CommandError('corpus "%s" does not exist' % corpusref)

			elif action == EXTRACT_FEATURES_ACTION:
				"""
				Extract features and metadata info from the corpus and save in database
				"""
				try:
					Workflow.extract_features_from_corpus(corpus)
				except corpus.DoesNotExist:
					raise CommandError('corpus "%s" does not exist' % corpusref)
			elif action == QUALEVAL:
				"""Evaluate the quality of a corpus"""
				opera = corpus.get_opera()
				valid = total = 0
				for opus in opera:
					Workflow.quality_check(opus)
				print("Done. ")
			elif action == COPY_DMOS_ACTION:
				"""Copy dmos files from one corpus to the other"""
				try:
					corpus_target = Corpus.objects.get(ref=options['corpus_target'])
					Workflow.copy_dmos(corpus, corpus_target)
				except Corpus.DoesNotExist:
					raise CommandError('Corpus "%s" does not exist' % options['corpus_target'])
				print("Done. ")
			elif action == FIX_PERMISSIONS_ACTION:
				group_editor = Group.objects.get(name=settings.EDITOR_GROUP)
				group_visitor = Group.objects.get(name=settings.VISITOR_GROUP)
				for corpus in Corpus.objects.all():					  
					print ("Fix permissions for corpus" + corpus.title)
					assign_perm('edit_corpus', group_editor, corpus)
					assign_perm('view_corpus', group_editor, corpus)
					if corpus.is_public:
						assign_perm('view_corpus', group_visitor, corpus)
						print ("Corpus is public")

				print("Done. ")
			else:
				self.stdout.write("Warning: unknown action : " +  action)
		else: # il y a un opus précis sur lequel travailler

			# opera = corpus.get_opera()
			# for opus in opera:
				# print(opus.ref)
			try:
				# opusref = options['corpus_ref'] + ":" + opusref
				opus = Opus.objects.get(ref=opusref)
			except Opus.DoesNotExist:
				raise CommandError('Opus "%s" does not exist' % opusref)
				exit
				
			self.stdout.write ("Found opus " + opus.title)

			if action == DISSONANCE_ACTION:
				#try:
				Workflow.cpt_opus_dissonances(opus)
				#except  Exception as ex:
				#	print ("Exception for opus " + opus.ref + " Message:" + str(ex))
				print ("Dissonances computed for " + opus.title + " (" + opus.ref +")")

			elif action == STATS_ACTION:
				if os.path.isfile( opus.musicxml.path):
					self.stdout.write("Essai de stats")
					stats = StatsDesc(opus)
					dico = stats.computeStats()
					for k,v in dico.items():
						if isinstance(v, str):
							self.stdout.write(k+" "+v)
						else:
							# distribution de notes
							self.stdout.write(k)
							self.stdout.write("  "+" ".join([str(a[0])+","+str(a[1]) for a in v]))
				else:
					self.stdout.write("Warning: invalid MusicXML file path for " + opus.title)
			elif action == QUALEVAL:
				"""Evaluate the quality of an opus"""
				Workflow.quality_check(opus)
				print("Done. ")
			elif action == DESCRIPTORJSON_ACTION:
				"""Produces a file with the descriptors, in json format"""
				Workflow.createJsonDescriptors(opus)
				print("Done. ")

			elif action == ANALYZE_OPUS_ACTION:
				"""
				Analyze all patterns in an opus to get the most frequent patterns
				"""
				try:
					mel_pat_dict, dia_pat_dict, rhy_pat_dict, mel_opus_dict, dia_opus_dict, rhy_opus_dict = Workflow.analyze_patterns_in_opus(opus)
					Workflow.patterns_statistics_analyze(mel_pat_dict, dia_pat_dict, rhy_pat_dict, mel_opus_dict, dia_opus_dict, rhy_opus_dict)
					#Note: since we are analyzing just one opus, mel/dia/rhy_opus_dict will be either empty or contain the opus ref. 
					print("Done.")
				except Opus.DoesNotExist:
					raise CommandError('Opus "%s" does not exist' % opusref)

			elif action == INDEX_ACTION:
				"""Index a specific opus"""
				print(opus, corpus)
				Workflow.index_opus(opus)
				print("Done. ")
			else:
					self.stdout.write("Warning: invalid action for opus " + opus.title + " : " + action)
