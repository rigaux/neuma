
import zipfile, os.path, io, json, sys, shutil

from manager.models import (Corpus, Opus, Descriptor, 
		OpusSource)
import os
import re
import subprocess
from django.core.files import File
from django.core.files.base import ContentFile


import ast

from django.conf import settings

# For computing score diffs
#from lib.musicdiff import DetailLevel
#from musicdiff.annotation import AnnScore
#from musicdiff.comparison import Comparison
#from musicdiff.visualization import Visualization


import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

from django.contrib.auth.models import User
from xml.dom import minidom


from lib.music.Score import *
import lib.music.source as source_mod

from lib.neumasearch.MusicSummary import MusicSummary
from neumasearch.IndexWrapper import IndexWrapper

# Music analysis module
import converter21
import music21 as m21

import logging

from scorelib.analytic_concepts import *

class Workflow:
	"""
		Operators triggered when a score is inserted / updated
	"""
	
	# Some codes for workflow options
	
	# To save an imported MEI a the reference source
	IMPOPT_SAVE_MEI="mei_as_source"

	def __init__(self) :
		 return
	
	"""
	@staticmethod
	def compute_opus_diff(opus, 
						detail= DetailLevel.GeneralNotesOnly, show_pdf=False):
		
		'''
		  Take two MEI files associated to the opus
		  Evaluate their difference withe musicdiff package
		  Return the list of operations
		'''
		
		if opus.mei is None:
			raise Exception(f"No MEI file in opus {opus.ref}")
			exit(1)

		# Use the new Humdrum/MEI importers from converter21 in place of the ones in music21...
		# Comment out this line to go back to music21's built-in Humdrum/MEI importers.
		converter21.register()

		source_mei = None
		for source in opus.opussource_set.all ():
			if source.ref == OpusSource.MEI_REF:
				source_mei = source.source_file
		
		if source_mei is None:
			print ("Unable to the find the reference MEI (there should be a ref_mei source)")

		# For converters, the MEI extension is required
		omr_path = "/tmp/omr.mei"
		ref_path = "/tmp/ref.mei"

		shutil.copyfile(opus.mei.path, omr_path)
		shutil.copyfile(source_mei.path, ref_path)
		
		# The following is taken from the musicdiff module, file __init__.py
		
		score1 = m21.converter.parse(omr_path, forceSource=True)
		score2 = m21.converter.parse(ref_path, forceSource=True)
		
		# scan each score, producing an annotated wrapper
		annotated_score1: AnnScore = AnnScore(score1, detail)
		annotated_score2: AnnScore = AnnScore(score2, detail)
	
		diff_list, _cost = Comparison.annotated_scores_diff(annotated_score1, 
														annotated_score2)

		# Mark the score with operations
		# you can change these three colors as you like...
		# Visualization.INSERTED_COLOR = 'red'
		# Visualization.DELETED_COLOR = 'red'
		# Visualization.CHANGED_COLOR = 'red'
		# color changed/deleted/inserted notes, add descriptive text for each change, etc
		Visualization.mark_diffs(score1, score2, diff_list)


		# Remove existing diffs
		OpusDiff.objects.filter(opus=opus).delete()

		opus_diff = OpusDiff (opus=opus)
		# Store the MusicXML file in the Comparison object
		# Generate and store the MEI file
		score1.write ("musicxml", "/tmp/mei1.xml")
		with open("/tmp/mei1.xml") as f:
			print ("Replace first MEI file")
			opus_diff.mei_omr = File(f,name="omr.mei")
			opus_diff.save()
		score2.write ("musicxml", "/tmp/mei2.xml")
		with open("/tmp/mei2.xml") as f:
			print ("Replace second MEI file")
			opus_diff.mei_ref= File(f,name="ref.mei")
			opus_diff.save()
			
		return len(diff_list)
	"""
	@staticmethod
	def index_corpus(corpus, recursion=True):
		"""
		(Re)create the index for all the opuses of a corpus (and its descendants
		if the recursion parameter is True)
		"""

		i=0
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
		print ("Descriptors produced")
		# Compute and store features
		#Workflow.extract_features_from_opus(opus)
		#print ("Features extracted")

		# Store the descriptors and the features in Elastic Search
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
	def extract_features_from_corpus(corpus, recursion=True):
		"""
		(Re)extract features and metadata for all the opuses of a corpus (and its descendants
		if the recursion parameter is True)
		"""

		for opus in Opus.objects.filter(corpus__ref=corpus.ref):
			Workflow.extract_features_from_opus(opus)

		# Recursive call
		if recursion:
			children = corpus.get_children(False)
			for child in children:
				Workflow.extract_features_from_corpus(child, recursion)


	@staticmethod
	def extract_features_from_opus(opus):
		'''
		Extract features from opus. 
		First get m21 stream from the original score of the opus, then extract features.
		'''
		try:
			#score = opus.get_score()
			if opus.mei:
				#print ("Load from MEI")
				with open (opus.mei.path, "r") as meifile:
					meiString = meifile.read()
					conv = m21.mei.MeiToM21Converter(meiString)
					m21_score = conv.run()
			elif opus.musicxml:
				#print ("Load from MusicXML")
				m21_score = m21.converter.parse(opus.musicxml.path)
			else:
				print("Exception caused by file format or when trying to access m21 object of opus " + opus.ref)
			
			# Extract features with m21 and save in database
			info = Workflow.extract_features_with_m21(opus, m21_score)
						
		except  Exception as ex:
			print ("Exception when trying to extract info from opus " + opus.ref + " Message:" + str(ex))

		# TODO: Store the descriptors in ElasticSearch
		#index_wrapper = IndexWrapper()
		#index_wrapper.index_opus(opus)

		return

	@staticmethod
	def extract_features_with_m21(opus, m21_score, forced=False):
		"""
		EXTRACT A LIST OF FEATURES FROM OPUS AND SAVE IN OPUSMETA
		"""
		print ("Producting features from opus " + opus.ref)

		info = {}
		
		# Get the current meta values. We do not want to compute twice,
		# except if "forced" recomputation
		opus_metas = []
		for m in opus.get_metas():
			opus_metas.append(m.meta_key)
		if not (OpusMeta.MK_KEY_TONIC in opus_metas) or forced:
			key = m21_score.analyze('key')
			info["key_tonic_name"] = key.tonic.name
			info["key_mode"] = key.mode

		if not (OpusMeta.MK_NUM_OF_PARTS in opus_metas) or forced:
			info["num_of_parts"] = len(m21_score.getElementsByClass(m21.stream.Part))
			
		if not (OpusMeta.MK_NUM_OF_MEASURES in opus_metas) or forced:
			info["num_of_measures"] = 0
			for part in m21_score.parts:
				info["num_of_measures"] += len(part)
		#flatten = m21_score.flatten()
		#can not use flatten, need to find another way...
		#info["num_of_notes"] TODO

		if not (OpusMeta.ML_INSTRUMENTS in opus_metas) or forced:
			info["instruments"] = []
			# TODO: JSON encode
			if m21.instrument.partitionByInstrument(m21_score) != None:
				for part in m21.instrument.partitionByInstrument(m21_score):
					info["instruments"].append(part.getInstrument().instrumentName)
						
		# TODO: this needs to be json encoded
		if not (OpusMeta.MK_LOWEST_PITCH_EACH_PART in opus_metas) or forced:
			pitchmin_eachpart = {}
			pitchmax_eachpart = {}
			p = m21.analysis.discrete.Ambitus()
			count = 0
			for part in m21_score.parts:
				count += 1
				pitchMin, pitchMax = p.getPitchSpan(part)
				partname = 'part'+str(count)
				pitchmin_eachpart[partname] = pitchMin.nameWithOctave
				pitchmax_eachpart[partname] = pitchMax.nameWithOctave
		
				info["lowest_pitch_each_part"] = json.dumps(pitchmin_eachpart)
				info["highest_pitch_each_part"] = json.dumps(pitchmax_eachpart)

		# the followings are float number instead of integer/string
		if not (OpusMeta.MK_AVE_MELODIC_INTERVAL in opus_metas) or forced:
			fe = m21.features.jSymbolic.AverageMelodicIntervalFeature(m21_score)
			info["average_melodic_interval"] = fe.extract().vector[0]

		if not (OpusMeta.MK_DIRECTION_OF_MOTION in opus_metas) or forced:
			fe = m21.features.jSymbolic.DirectionOfMotionFeature(m21_score)
			info["direction_of_motion"] = fe.extract().vector[0]

		if not (OpusMeta.MK_MOST_COMMON_NOTE_QUARTER_LENGTH in opus_metas) or forced:
			fe = m21.features.native.MostCommonNoteQuarterLength(m21_score)
			info["most_common_note_quarter_length"] = fe.extract().vector[0]

		if not (OpusMeta.MK_RANGE_NOTE_QUARTER_LENGTH in opus_metas) or forced:
			fe = m21.features.native.RangeOfNoteQuarterLengths(m21_score)
			info["range_note_quarter_length"] = fe.extract().vector[0]

		if not (OpusMeta.MK_INIT_TIME_SIG in opus_metas) or forced:
			fe = m21.features.jSymbolic.InitialTimeSignatureFeature(m21_score)
			#print("\nInitial time signature:", fe.extract().vector)
			info["initial_time_signature"] = json.dumps(fe.extract().vector)

		 #print("Info:", info)
		
		# At last, store in postgres
		for item in info:
			opus.add_meta(item, info[item])
			# print("added", item)
		return info

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
				music_summary = MusicSummary.get_music_summary(score)
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
	def import_zip(zip, parent_corpus, corpus_ref, options=[]):
		list_imported = Corpus.import_from_zip(zip, parent_corpus, corpus_ref)
		
		if Workflow.IMPOPT_SAVE_MEI in options:
			for opus in list_imported:
				print (f"Saving MEI file of {opus.ref} as reference MEI")
				opus.copy_mei_as_source()
		# Produce descriptors and index the corpus in ElasticSearch
		print (f"\n\nINDEXING IMPORTED OPUSES")
		for opus in list_imported:
			Workflow.index_opus(opus)
		return list_imported
	
	@staticmethod 
	def copy_dmos(source, target):
		print (f"Copy DMOS files from corpus '{source.ref}' to corpus '{target.ref}'")
		for opus in source.get_opera():
			print (f"Checking opus {opus.ref}")
			# Is there a corresponding opus in the target corpus
			opus_target_ref = target.ref + ":" + opus.local_ref()
			try:
				opus_target = Opus.objects.get(ref=opus_target_ref)
			except Opus.DoesNotExist:
				print (f"\tNo Opus {opus_target_ref} in the target Corpus. Ignored")
				continue 
			
			try:
				source = OpusSource.objects.get(opus=opus,ref=source_mod.OpusSource.IIIF_REF)
			except OpusSource.DoesNotExist:
				print (f"\tNo source IIIF for this Opus. Ignored")
				continue 
			
			if source.source_file:
				with open(source.source_file.path, "r") as f:
					dmos_data = f.read()
				print (f"\tFound a source IIIF with a DMOS file for this Opus.")
				try:
					source_target = OpusSource.objects.get(opus=opus_target,ref=source_mod.OpusSource.IIIF_REF)
					source_target.source_file.save("dmos.json", ContentFile(dmos_data))
					print (f"\tSUCCESS. DMOS file has been copied for opus {opus_target_ref}.")
					# And now, parse...
					opus_target.parse_dmos()
				except OpusSource.DoesNotExist:
					print (f"\tSource IIIF in target opus does not exist")
					continue 
			else:
				print (f"\tNo DMOS data in this source. Ignored")
				continue 
				
		return

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
