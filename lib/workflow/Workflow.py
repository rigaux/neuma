
from manager.models import Corpus, Opus, Descriptor, Annotation, AnalyticModel, AnalyticConcept, Patterns
import os
import re
import subprocess
from django.core.files import File
from django.core.files.base import ContentFile
import json
import sys
from neumautils.duration_tree import *

import ast
from scorelib import local_settings

from search.IndexWrapper import IndexWrapper

import zipfile, os.path, io

import logging


# Get an instance of a logger
logger = logging.getLogger(__name__)


from django.contrib.auth.models import User
from xml.dom import minidom

# To communicate with Neuma
from lib.neuma.rest import Client

from lib.music.Score import *

# Music analysis module
from music21 import converter
import logging
# from lib.music.counterpoint import  pitchCollections, dissonanceAnalysis
from lib.music.counterpoint import  pitchCollections


from django_q.tasks import *
from scorelib.analytic_concepts import *

from quality.lib.Processor import QualityProcessor

from transcription.models import Grammar, GrammarRule


class Workflow:
	"""
		Operators triggered when a score is inserted / updated
	"""
	
	def __init__(self) :
		 return
	

	@staticmethod
	def produce_mei(corpus, recursion=True):
		"""
		Produce the MEI file by applying an XSLT tranforsm to the MusicXML doc.
		"""
		print("Produce all missing MEI file for corpus " + corpus.title)
		for opus in Opus.objects.filter(corpus__ref=corpus.ref):
			Workflow.produce_opus_mei(opus)
		print("MEI files produced for corpus " + corpus.title)

		# Recursive call
		if recursion:
			children = corpus.get_children(False)
			for child in children:
				Workflow.produce_mei(child, recursion)

	@staticmethod
	def produce_opus_mei(opus, replace=False):
		# First take the script template depending on the OS
		if os.name == 'nt': #Windows
			with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei.bat')) as script_file:
				script_file = script_file.read()
		else:
			with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei.sh')) as script_file:
				script_file = script_file.read()
				
		# Get the script template by replacing the deployment-dependent paths
		sfile = script_file.replace ("{saxon_path}", os.path.join(settings.BASE_DIR, "lib","saxon")).replace("{xsl_path}", settings.SCRIPTS_ROOT).replace("{tmp_dir}", settings.TMP_DIR)

		# Take care: we never replace an existing MEI unless explicitly allowed
		if opus.musicxml and (not opus.mei or replace):
			try:
				with open(opus.musicxml.path) as musicxml_file:
					musicxml = musicxml_file.read()
						
				# Remove the DTD: avoids Web accesses, timeouts, etc.
				pattern = re.compile("<!DOCTYPE(.*?)>", re.DOTALL)
				mxml_without_type = re.sub(pattern, "", musicxml)
				# Write the MusicXML without DTD in the tmp area
				mxml_file = open(os.path.join(settings.TMP_DIR, "score.xml"),"w")
				mxml_file.write(mxml_without_type)
				mxml_file.close()
						
				# Create and run a script to convert the MusicXML with XSLT
				convert_file = sfile.replace ("{musicxml_path}", os.path.join(settings.TMP_DIR,"score.xml")).replace("{opus_ref}", opus.ref)
				if os.name == 'nt':
					script_name = f = os.path.join(settings.TMP_DIR, "cnv_mei_" + str(opus.id) + ".bat") #for windows
				else:
					script_name = f = os.path.join(settings.TMP_DIR, "cnv_mei_" + str(opus.id) + ".sh")
				f = open(script_name,"w")
				f.write(convert_file)
				f.close()
				print ("Conversion script created in " + script_name)
				if os.name != 'nt':
					subprocess.call(["chmod", "a+x", script_name])
				else: #on windows no need to chmod
					print("Detected OS: Windows")

				# Now, run the script
				if os.name == 'nt': #if it's window
					result = subprocess.call(script_name)
				else:
					result = subprocess.call(script_name)
				if result == 0:
					print ("Success : import the MEI file")
					with open(os.path.join(settings.TMP_DIR ,"mei.xml")) as mei_file:
						opus.mei.save ("mei.xml", File(mei_file))
				else:
					print ("Error converting the MusicXML file")
			except  Exception as ex:
				print ("Exception for opus " + opus.ref + " Message:" + str(ex))
		else:
			logger.info("MEI file already exists: we do not override it")
			
	@staticmethod
	def produce_temp_mei(path_to_musicxml, mei_number):
		"""
		Temporary produce and save a MEI file (with name: {mei_name}) from a music xml file.
		This does not involve the database
		mei_name : can be either the integer 1 or 2
		return: the path to the MEI file
		"""
		# First take the script template depending on the OS
		if os.name == 'nt': #Windows still to implement
			with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei.bat')) as script_file:
				script_file = script_file.read()
		else:
			with open(os.path.join(settings.SCRIPTS_ROOT, 'mxml2mei_param_name.sh')) as script_file:
				script_file = script_file.read()
		
		#create the correct mei name
		if mei_number == 1:
			mei_name = "comp_temp_mei_1"
		elif mei_number == 2:
			mei_name = "comp_temp_mei_2"
		else:
			 raise Exception("mei_name can be either the integer 1 or 2")
		# Get the script template by replacing the deployment-dependent paths
		# WARNING: Highly risky function because it will delete files from the memory
		sfile = script_file.replace ("{saxon_path}", os.path.join(settings.BASE_DIR, "lib","saxon")).replace("{xsl_path}", settings.SCRIPTS_ROOT).replace("{tmp_dir}", settings.TMP_DIR).replace("{mei_name}", mei_name)


		# Produce the MEI
		try:
			with open(path_to_musicxml) as musicxml_file: #check if the file exist
				musicxml = musicxml_file.read()
			
			# Remove the DTD: avoids Web accesses, timeouts, etc.
			pattern = re.compile("<!DOCTYPE(.*?)>", re.DOTALL)
			mxml_without_type = re.sub(pattern, "", musicxml)
			# Write the MusicXML without DTD in the tmp area
			mxml_file = open(os.path.join(settings.TMP_DIR, "temp_xml_score.xml"),"w")
			mxml_file.write(mxml_without_type)
			mxml_file.close()
					
			# Create and run a script to convert the MusicXML with XSLT
			if os.name == 'nt':
				script_name = f = os.path.join(settings.TMP_DIR, "cnv_temp_mei.bat") #for windows
			else:
				script_name = f = os.path.join(settings.TMP_DIR, "cnv_temp_mei.sh")
			with open(script_name,"w") as f:
				f.write(sfile)
			if os.name != 'nt':
				subprocess.call(["chmod", "a+x", script_name])
			else: #on windows no need to chmod
				print("Detected OS: Windows")

			# Now, run the script
			if os.name == 'nt': #if it's window
				result = subprocess.call(script_name)
			else:
				result = subprocess.call(script_name)
			if result == 0:
				print ("Success : created the temporary MEI file for comparison")
				return {"path_to_temp_mei": str(os.path.join(settings.TMP_DIR ,mei_name + ".xml"))}
		except  Exception as ex:
			print ("Exception: " + str(ex))

	@staticmethod
	def index_corpus(corpus, recursion=True):
		"""
		(Re)create the index for all the opuses of a corpus (and its descendants
		if the recursion parameter is True)
		"""

		for opus in Opus.objects.filter(corpus__ref=corpus.ref):
			Workflow.index_opus(opus)

		# Recursive call
		if recursion:
			children = corpus.get_children(False)
			for child in children:
				Workflow.index_corpus(child, recursion)
				
	@staticmethod
	def propagate(corpus, recursion=True):
		"""
		If the licence notice is not null: propagate it to the corpus children
		Same for the composer
		"""
		
		children = corpus.get_children(False)
		if corpus.licence  != None:
			for child in children:
				child.licence = corpus.licence
				child.save()
		if corpus.copyright  != None and corpus.copyright != '':
			for child in children:
				child.copyright = corpus.copyright
				child.save()
		if corpus.composer  != None:
			for child in children:
				child.composer = corpus.composer
				child.save()
		# Recursive call
		if recursion:
			for child in children:
				Workflow.propagate(child, recursion)

	@staticmethod
	def index_opus(opus):
		'''
		   Index an opus
		   
		   This functions produces the Opus descriptors which are
		   stored in the DB. It then scans these descriptors and
		   sends them to ElasticSearch
		'''
		
		# Produce the Opus descriptors
		Workflow.produce_opus_descriptor(opus)
		
		# Store the descriptors in Elastic Search
		index_wrapper = IndexWrapper()
		index_wrapper.index_opus(opus)

	@staticmethod
	def patterns_statistics_analyze(mel_dict, dia_dict, rhy_dict, mel_opus_dict, dia_opus_dict, rhy_opus_dict):
		"""
		Analyze statistics based on all patterns in the opus/corpus/library, 
		such as top 15 common patterns, or output all patterns
		"""

		#We define the low threshold: if it appears less than 10 times in the library, it is not a pattern.

		#Output every pattern appeared in csv
		
		mel_sorted = sorted(mel_dict.items(), key=lambda x: x[1], reverse=True)
		with open("melodic_patterns_sorted.csv", "w") as out_f:
				for ele in mel_sorted:
						print(ele[0], ",", ele[1], file = out_f)
						#if ele[1] < 10: break

		dia_sorted = sorted(dia_dict.items(), key=lambda x: x[1], reverse=True)
		with open("diatonic_patterns_sorted.csv", "w") as out_f:
				for ele in dia_sorted:
						print(ele[0], ",", ele[1], file = out_f)
						#if ele[1] < 10: break

		rhy_sorted = sorted(rhy_dict.items(), key=lambda x: x[1], reverse=True)
		with open("rhythmic_patterns_sorted.csv", "w") as out_f:
				for ele in rhy_sorted:
						print(ele[0], ",", ele[1], file = out_f)
						#if ele[1] < 10: break

		'''
		print("30 most frequent melodic patterns so far:")
		cnt = 0
		#sort elements by their total appearance number 
		for ele in sorted(mel_dict, key=mel_dict.get, reverse=True):
			print("Pattern ",ele, " with total appearance:", mel_dict[ele])
			print("appeared in", len(mel_opus_dict[ele]), "opuses.\n")
			#print("which are:", mel_opus_dict[ele])
			cnt += 1
			#only print the top 15 results
			if cnt >= 30: break

		print("\n\n30 most frequent diatonic patterns so far:")
		cnt = 0
		#sort elements by their total appearance number
		for ele in sorted(dia_dict, key=dia_dict.get, reverse=True):
			print("Pattern ",ele, " with total appearance:", dia_dict[ele])
			print("appeared in", len(dia_opus_dict[ele]), "opuses.\n")
			#print("which are:", dia_opus_dict[ele])
			cnt += 1
			#only print the top 15 results
			if cnt >= 30: break

		print("\n\n30 most frequent rhythmic patterns so far:")
		cnt = 0
		#sort elements by their total appearance number
		for ele in sorted(rhy_dict, key=rhy_dict.get, reverse=True):
			print("Pattern ",ele, " with total appearance:", rhy_dict[ele])
			print("appeared in", len(rhy_opus_dict[ele]), "opuses.\n")
			#print("which are:", rhy_opus_dict[ele])
			cnt += 1
			#only print the top 15 results
			if cnt >= 30: break
		'''

	@staticmethod
	def analyze_patterns(corpus, recursion = True):
		'''
		Analyze all pattern to get statistical data of frequent patterns
		'''
		for opus in Opus.objects.filter(corpus__ref=corpus.ref):
			mel_pat_dict, dia_pat_dict, rhy_pat_dict, mel_opus_dict, dia_opus_dict, rhy_opus_dict = Workflow.analyze_patterns_in_opus(opus)

		# Recursive call
		if recursion:
			children = corpus.get_children(False)
			for child in children:
				Workflow.analyze_patterns(child, recursion)

		try:
			Workflow.patterns_statistics_analyze(mel_pat_dict, dia_pat_dict, rhy_pat_dict, mel_opus_dict, dia_opus_dict, rhy_opus_dict) 
		except:
			#When the analysis finish, no value would be assigned to mel_pat_dict etc.. thus simply return void
			return

	@staticmethod
	def analyze_patterns_in_opus(opus):
		'''
		Analyze melodic, diatonic and rhythmic patterns within an opus and store statistics
		'''
		print ("Analyze patterns in opus " + opus.ref)

		try:
			score = opus.get_score()
		except:
			print("Could not get score for opus" + opus.ref)
			return {},{},{},{},{},{}

		#If there is an error while tranforming MEI into XML format, skip this opus
		if score.m21_score == None:
			return {},{},{},{},{},{}

		# First, compute the music summary and store it as a file
		music_summary = score.get_music_summary()
		music_summary.opus_id = opus.ref
		opus.summary.save("summary.json", ContentFile(music_summary.encode()))

		# Find patterns within each Voice of an Opus
		for part_id, part in music_summary.parts.items():
			for voice_id, voice in part.items():
				for n in range(3, 12):
					# Melody descriptor
					mel_descr = voice.get_melody_encoding(False, n)
			
					# 'N' is used as segregation between patterns in descriptor
					pattern_list = mel_descr.split("N")

					#not recording opus ref for each pattern anymore bc there are too many patterns
					#mel_pat_dict, mel_opus_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.MELODY_DESCR)
					mel_pat_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.MELODY_DESCR)

					#Diatonic descriptor
					dia_descr = voice.get_diatonic_encoding(False, n)
				
					pattern_list = dia_descr.split("N")

					#dia_pat_dict, dia_opus_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.DIATONIC_DESCR)
					dia_pat_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.DIATONIC_DESCR)
 
					# Rhythm descriptor
					rhy_descr = voice.get_rhythm_encoding(n)
				
					###rhythm_encoding = self.rhythms_to_ngrams(self.get_rhythms())
					pattern_list = rhy_descr.split("N")
				
					#rhy_pat_dict, rhy_opus_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.RHYTHM_DESCR)
					rhy_pat_dict = Workflow.get_patterns_from_descr(pattern_list, opus, part_id, voice_id, settings.RHYTHM_DESCR)

		return mel_pat_dict, dia_pat_dict, rhy_pat_dict, {}, {}, {}#, mel_opus_dict, dia_opus_dict, rhy_opus_dict
	
	@staticmethod
	def get_patterns_from_descr(pattern_list, opus, part_id, voice_id, descriptor):
		"""
		Iterate over the list of patterns to get statistical information of every pattern in a voice
		"""

		#if pattern list is empty, return:
		if pattern_list == [""] or pattern_list == None:
			return {}, {}

		for curr_pattern in pattern_list:
			#if it is an invalid pattern, skip
			if curr_pattern == '' or curr_pattern == ' ': continue
			
			pattern = Patterns()
			pattern.opus = opus
			pattern.part = part_id
			pattern.voice = voice_id
			pattern.content_type = descriptor
			
			#Strip spaces in the beginning and the end to get the pattern in a "clean" way
			clean_pat = curr_pattern
			clean_pat = clean_pat.strip()
			pattern.value = clean_pat
			
			if descriptor == settings.MELODY_DESCR:
				#If the pattern is already in dictionary, total number +=1
				if clean_pat in pattern.mel_pattern_dict:
					pattern.mel_pattern_dict[clean_pat] += 1
					#if opus.ref not in pattern.mel_opuses[clean_pat]:
					#	pattern.mel_opuses[clean_pat].append(opus.ref)
				#Otherwise save the pattern
				else:
					pattern.mel_pattern_dict[clean_pat] = 1
					#save all opus reference for each pattern...
					#pattern.mel_opuses[clean_pat] = []
					#pattern.mel_opuses[clean_pat].append(opus.ref)
				
			elif descriptor == settings.DIATONIC_DESCR:
				#If the pattern is already in dictionary, total number +=1, and save the opus ref
				if clean_pat in pattern.dia_pattern_dict:
					pattern.dia_pattern_dict[clean_pat] += 1
					#if opus.ref not in pattern.dia_opuses[clean_pat]:
					#	pattern.dia_opuses[clean_pat].append(opus.ref)
				#Otherwise save the pattern
				else:
					pattern.dia_pattern_dict[clean_pat] = 1
					#save all opus ref for each pattern... 
					#pattern.dia_opuses[clean_pat] = []
					#pattern.dia_opuses[clean_pat].append(opus.ref)

			elif descriptor == settings.RHYTHM_DESCR:
				#If the pattern is already in dictionary, total number +=1
				if clean_pat in pattern.rhy_pattern_dict:
					pattern.rhy_pattern_dict[clean_pat] += 1
					#if opus.ref not in pattern.rhy_opuses[clean_pat]:
					#	pattern.rhy_opuses[clean_pat].append(opus.ref)
					#Otherwise save the pattern
				else:
					pattern.rhy_pattern_dict[clean_pat] = 1
					#Save all opus ref for each pattern..
					#pattern.rhy_opuses[clean_pat] = []
					#pattern.rhy_opuses[clean_pat].append(opus.ref)

		try:
			if descriptor == settings.MELODY_DESCR:
				return pattern.mel_pattern_dict#, pattern.mel_opuses

			elif descriptor == settings.DIATONIC_DESCR:
				return pattern.dia_pattern_dict#, pattern.dia_opuses

			elif descriptor == settings.RHYTHM_DESCR:
				return pattern.rhy_pattern_dict#, pattern.rhy_opuses

		except Exception as ex:
			print ("Exception for opus " + opus.ref + " Message:" + str(ex))
 
	@staticmethod
	def produce_opus_descriptor(opus, affiche=False):
		"""
		Produce the descriptors for an opus.
		
		A "music summary" containing all the necessary info to perform
		searches is stored as a JSON file with the Opus. From
		this summary, descriptors are extracted for each voice
		and stored in the DB.
		
		In its current implementation, the only descriptors is related to the
		melodic profile of each voice. Optionally, we also store the lyrics if present.
		"""
		print ("Produce descriptors for opus " + opus.ref)
		descriptors_dict = {}
		try:
				score = opus.get_score()

				#If there is error while transforming MEI into XML format, skip this opus
				if score.m21_score == None:
					return

				# First, compute the music summary and store it as a file
				music_summary = score.get_music_summary()
				music_summary.opus_id = opus.ref
				#opus.summary.save("summary.json", ContentFile(music_summary.encode()))
				#print (json.dumps(json_summary, indent=4, separators=(',', ': ')))
				types = "melodic", "diatonic", "rhythmic", "notes"
				for atype in types:
					descriptors_dict[atype] = {}

				# Clean the current descriptors
				Descriptor.objects.filter(opus=opus).delete()
		
				# Next, compute the descriptors for each Voice
				for part_id, part in music_summary.parts.items():
					for voice_id, voice in part.items():
						# Melody descriptor
						music_descr = voice.get_melody_encoding()
						# print ("Voice " + str(voice_id)) # + " NGRAM encoding: " + music_descr)
						# Store in Postgres
						descriptor = Descriptor()
						descriptor.opus = opus
						descriptor.part = part_id
						descriptor.voice = voice_id
						descriptor.type = settings.MELODY_DESCR
						descriptor.value = music_descr
						if not affiche:
							descriptor.save()
						else:
							# print(descriptor.to_dict())
							descriptors_dict["melodic"][str(voice_id)]=descriptor.to_dict()

						#Diatonic descriptor, store in Postgres
						diatonic_descr = voice.get_diatonic_encoding()
						descriptor = Descriptor()
						descriptor.opus = opus
						descriptor.part = part_id
						descriptor.voice = voice_id
						descriptor.type = settings.DIATONIC_DESCR
						descriptor.value = diatonic_descr
						if not affiche:
							descriptor.save()
						else:
							# print(descriptor.to_dict())
							descriptors_dict["diatonic"][str(voice_id)]=descriptor.to_dict()
						
						# Rhythm descriptor
						rhythm_descr = voice.get_rhythm_encoding()
						descriptor = Descriptor()
						descriptor.opus = opus
						descriptor.part = part_id
						descriptor.voice = voice_id
						descriptor.type = settings.RHYTHM_DESCR
						descriptor.value = rhythm_descr
						if not affiche:
							descriptor.save()
						else:
							# print(descriptor.to_dict())
							descriptors_dict["rhythmic"][str(voice_id)]=descriptor.to_dict()
						
						# Notes descriptor
						notes_descr = voice.get_note_encoding()
						descriptor = Descriptor()
						descriptor.opus = opus
						descriptor.part = part_id
						descriptor.voice = voice_id
						descriptor.type = settings.NOTES_DESCR
						descriptor.value = notes_descr
						if not affiche:
							descriptor.save()
						else:
							# print(descriptor.to_dict())
							descriptors_dict["notes"][str(voice_id)]=descriptor.to_dict()
			   
				# Hack: the M21 parser does not supply lyrics. Use the MusicXML for the moment				   
				
				if opus.musicxml:
					score = Score()
					score.load_from_xml(opus.musicxml.path, "musicxml")
				
				voices = score.get_all_voices()
				for voice in voices:
						if voice.has_lyrics():
							# Store in Postgres
							descriptor = Descriptor()
							descriptor.opus = opus
							descriptor.part = settings.ALL_PARTS
							descriptor.voice = voice.id
							descriptor.type = settings.LYRICS_DESCR
							descriptor.value = voice.get_lyrics()
							descriptor.save()

		except  Exception as ex:
			print ("Exception when trying to write descriptor for opus " + opus.ref + " Message:" + str(ex))

		return descriptors_dict

	@staticmethod 
	def import_zip(zip, parent_corpus, corpus_ref):
		list_imported = Corpus.import_from_zip(zip, parent_corpus, corpus_ref)
		
		# Produce descriptors and index the corpus in ElasticSearch
		#Workflow.index_corpus(upload.corpus, True)
		return list_imported
	
	@staticmethod 
	def export_from_es(output_dir):
		print ("Exporting all JSON files from Elastic search in dir %s" % output_dir)
		index_wrapper = IndexWrapper()
		index_wrapper.export_all(output_dir)

		return


	@staticmethod
	def async_import (upload):
		"""Create a task to run the import asynchronuously """
		
		#task_id = async("workflow_import_zip", upload)
		
	@staticmethod
	def quality_check(opus):

		# try:
		QualityProcessor.applyToOpus(opus)

	# except Exception as e:
	#	print("Following error encountered on Opus "+str(opus))
	#	print("	> "+str(e))

	@staticmethod
	def compute_grammar(corpus):
		grammar = Grammar.objects.filter(corpus=corpus)[0]
		print("Retrieving grammar representation from database")
		grammar_str = grammar.get_str_repr(allow_zero_weights= True)
		print("Retrieving the rules from database")
		rules = GrammarRule.objects.filter(grammar=grammar).order_by('creation_timestamp')
		rules_size = rules.count()

		with open(os.path.join('transcription', 'grammars', 'grammar.txt'), 'w') as f:
			f.write(grammar_str)
		print("Grammar Written")
		failure_counter = 0  # to keep track of the number of failure
		opera = corpus.get_opera()
		flatMeasuresDurations = []
		time_signature = []  # initialized empty, it is update in the first bar
		for opus in opera:
			score = Score()
			print("Title : " + opus.title)
			score.load_from_xml(opus.mei.path, "mei")

			# save the duration tree for each bar
			for part_index, part in enumerate(score.m21_score.parts):  # loop through parts
				for measure_index, measure_with_rests in enumerate(part.getElementsByClass('Measure')):
					if measure_with_rests.timeSignature is not None:  # update the time_signature if there is a time_signature change
						time_signature.append(measure_with_rests.timeSignature)
					if len(measure_with_rests.voices) == 0:  # there is a single Voice ( == for the library there are no voices)
						measure = delete_rests(measure_with_rests)
						flatMeasuresDurations.append(
							list(measure.getElementsByClass('GeneralNote')))
					else:  # there are multiple voices (or an array with just one voice)
						for voice_with_rest in measure_with_rests.voices:
							voice = delete_rests(voice_with_rest)
							# print(list(voice.getElementsByClass('GeneralNote')))
							flatMeasuresDurations.append(
								list(voice.getElementsByClass('GeneralNote')))

		# process and sum over all the bars
		time_signature_str = str(time_signature[0].numerator) + "/" + str(time_signature[0].denominator)
		print("Number of rules: " + str(rules_size))
		sum_rule = {}  # long enough vector. zip will cut it

		for dur in flatMeasuresDurations:
			try:
				nested_list_dur = notes_to_nested_list(dur, std_div=std_div1, tempo=time_signature_str)
				num_list = dur_to_number(nested_list_dur)
				c_input = preprocess_number_list(num_list)
				grammar_input_path = local_settings.GRAMMAR_INPUT_PATH
				script_path = local_settings.SCHEMAS_PATH
				config_path= local_settings.QPARSELIB_CONFIG_PATH
				unix_command = "{0} -i {1} -tree \"{2}\" -config {3} -v 0".format(script_path, grammar_input_path,
																		  c_input, config_path)
				print(unix_command)
				if os.name == 'nt': #on windows, we call the ubuntu bash
					# print("windows system detected")
					c_output = subprocess.check_output(["bash", "-c", unix_command])
				else:
					# print("Unix system detected")
					c_output = subprocess.check_output(unix_command, shell=True)
				# print(c_output.decode("utf-8").splitlines()[2])
				rule_list = json.loads(c_output.decode("utf-8").splitlines()[2]) #some useless stuff in the first 2 rows
				# print(rule_list)
				sum_rule = { k: sum_rule.get(k, 0) + rule_list.get(k, 0) for k in set(sum_rule) | set(rule_list) } #"sum" the two dictionaries
				# print("Did it!")
			except:
				print("Parsing failed for durations: ")
				print([e.duration.quarterLength for e in dur])
				failure_counter += 1

		# add the not-normalized weigth to the grammar
		for i, r in enumerate(rules):
			if str(i) not in sum_rule:
				r.weight = 0
				r.save()
			else:
				r.weight = sum_rule[str(i)]
				r.save()
		# normalize the weight for each head
		heads = GrammarState.objects.filter(grammar=grammar)
		for head in heads:
			rules = GrammarRule.objects.filter(grammar=grammar, head=head).all()
			weight_sum = sum([rule.weight for rule in rules])
			for i, r in enumerate(rules):
				unnormalized_weight = r.weight
				if unnormalized_weight != 0:  # that is true only if weight sum is >0, so that shoul avoid divisions by 0
					r.weight = unnormalized_weight / weight_sum
					r.save()
		# save the number of failures
		grammar.parse_failures_ratio = failure_counter / len(flatMeasuresDurations)
		print("Failure counter= " + str(failure_counter / len(flatMeasuresDurations)))
		grammar.save()

		# print the weighted grammar
		grammar_str = Grammar.objects.filter(corpus=corpus)[0].get_str_repr()

		with open(os.path.join('transcription', 'grammars', 'weighted_grammar.txt'), 'w') as f:
			f.write(grammar_str)

def createJsonDescriptors(opus):
		"""returns the Json representation of an opus"""
		opusdict = {}
		opusdict["opusref"] = str(opus.ref)
		opusdict["opusurl"] = "http://neuma.huma-num.fr/home/opus/"+str(opus.ref)

		types = "melodic", "diatonic", "rhythmic", "notes"

		descriptors = Workflow.produce_opus_descriptor(opus,affiche=True)
		# print(descriptors.items())

		for atype in types: 
			l = []
			for voice, descrip in descriptors[atype].items():
				l.append(descrip["value"])

			opusdict[atype] = l

		# Serializing json 
		json_object = json.dumps(opusdict, indent = 4)
		# Writing to sample.json
		filename = str(opus.ref).replace(":", "-") + ".json"
		with open(filename, "w") as outfile:
			outfile.write(json_object)

#
# A top level function that calls import zip. Necessary for multi thearing, otherwise
# we get a pickle erro

def workflow_import_zip(upload, do_import=True):
	Workflow.import_zip(upload, do_import)
