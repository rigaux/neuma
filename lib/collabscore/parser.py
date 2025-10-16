
# import the logging library
import logging
import sys
import json
import jsonref
from jsonref import JsonRef
import jsonschema


from fractions import Fraction

import lib.collabscore.editions as editions_mod

import lib.music.Score as score_model
import lib.music.Voice as voice_model
import lib.music.events as score_events
import lib.music.notation as score_notation
import lib.music.annotation as annot_mod
import lib.music.constants as constants_mod
import lib.music.source as source_mod

from .constants import *
from .editions import Edition
from lib.music.source import Manifest
from .utils import Headers, DmosVoice

# Get an instance of a logger
# See https://realpython.com/python-logging/

#logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Create file handler
f_handler = logging.FileHandler(__name__ + '.log')
f_handler.setLevel(logging.WARNING)
# Create formatters and add it to handlers
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
# Add handlers to the logger
logger.addHandler(f_handler)

# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.WARNING)
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
#logger.addHandler(c_handler)

# For generated signatures
PSEUDO_SIGN_ID="pseudo_sign"
PSEUDO_SIGN_COUNTER=0


def set_logging_level(level):
	logger.setLevel(level)

class ParserConfig:
	"""
	  Defines the part of the input which are processed. 
	  Useful for testing
	"""
	def __init__(self, config={}):
		# Input: a dict taken from a config file
		if "log_level" in config:
			self.log_level=config["log_level"]
		else:
			self.log_level=logging.WARNING
		set_logging_level(self.log_level)
		
		if "page_min" in config:
			self.page_min = config["page_min"]
		else:
			self.page_min = 0
		if "page_max" in config:
			self.page_max = config["page_max"]
		else:
			self.page_max = sys.maxsize
		if "system_min" in config:
			self.system_min = config["system_min"]
		else:
			self.system_min = 0
		if "system_max" in config:
			self.system_max = config["system_max"]
		else:
			self.system_max = sys.maxsize
		if "measure_min" in config:
			self.measure_min = config["measure_min"]
		else:
			self.measure_min = 0
		if "measure_max" in config:
			self.measure_max = config["measure_max"]
		else:
			self.measure_max = sys.maxsize

	def print (self):
		print (f"\t**Parser configuration**\n\t\tLog level={self.log_level}\n" +
		         f"\t\tpage_min={self.page_min} -- page_max={self.page_max}\n" +
		         f"\t\tsystem_min={self.system_min} -- system_max={self.system_max}\n" +
			     f"\t\tmeasure_min={self.measure_min} -- measure_max={self.measure_max}\n")
			
	def in_range(self, page_no, system_no=None, measure_no=None):
		# Testing page
		if page_no < self.page_min or  page_no > self.page_max:
			return False
		if system_no is None:
			# Ok we are in page range
			return True
		
		# Testing system
		if (page_no == self.page_min and system_no < self.system_min) or (
				page_no == self.page_max and system_no > self.system_max):
			return False
		if measure_no is None:
			# Ok we are in page-system range
			return True
		
		# Testing measure
		if page_no == self.page_min and system_no == self.system_min and measure_no < self.measure_min:
			return False 
		if page_no == self.page_max and system_no == self.system_max and measure_no > self.measure_max:
			return False
		# All good !
		return True

class CollabScoreParser:
	"""

		A class to parse a JSON document provided by the OMR tool 
		and to produce encoded scores

	"""

	def __init__(self, schema_file_path, base_uri=""):
		"""
		   Load the schema of OMR json files, for type checking
		   
		   See https://python-jsonschema.readthedocs.io/en/latest/
		   
		   To check the schema: http://www.jsonschemavalidator.net/
		"""
		
		self.error_messages = []
		
		# Check schema via class method call. Works, despite IDE complaining
		logger.info (f'Loading schema file {schema_file_path} from {base_uri}')
		# Might raise an exception
		try:
			self.schema  = jsonref.load_uri(schema_file_path, base_uri=base_uri)
			logger.info (f'Schema loaded')
			# The schema contains references to sub-files that need to be solved
			self.resolver = jsonschema.RefResolver(referrer=self.schema, 
										base_uri=base_uri)
			self.validator = jsonschema.Draft7Validator (self.schema, resolver=self.resolver)
		except jsonschema.ValidationError as ex:
			logger.error (f'Error loading schema file {ex}')
			errors = sorted(self.validator.iter_errors(self.schema), key=lambda e: e.path)
			str_errors = ""
			for e in errors:
				path = "/"
				for p in e.absolute_path:
					path += str(p) + '/' 
				str_errors += " Error : " + e.message + " (path " + path + ")"
			raise Exception ("Schema  validation error: " + str_errors)
		except jsonschema.SchemaError as ex:
			errors = sorted(self.validator.iter_errors(self.schema), key=lambda e: e.path)
			str_errors = "/"
			for e in errors:
				path = ""
				for p in e.absolute_path:
					path += str(p) + '/' 
				str_errors += " Error : " + e.message + " (path " + path + ")"
			raise Exception ("Schema  validation error: " + str_errors)


	def validate_data (self, json_content):
		# Might raise an exception
		try:
			jsonschema.validate (instance=json_content, 
							schema=self.schema, 
							resolver=self.resolver)
		except jsonschema.ValidationError as ex:
			self.error_messages = self.collect_errors(json_content, "Data validation errror")
			return False
		except jsonschema.SchemaError as ex:
			self.error_messages = self.collect_errors(json_content, "Schema validation errror")
			return False
		# No pb
		return True
	
	def collect_errors (self, json_content, context):
		''' 
		Put errors found in an exception in a list
		'''
		errors_list=[]
		errors = sorted(self.validator.iter_errors(json_content), key=lambda e: e.path)
		for e in errors:
			path = "/"
			for p in e.absolute_path:
				path += str(p) + '/' 
			errors_list.append(f"{context}: {e.message} at path {path}")
		return errors_list

"""
  Utility classes
"""

class OmrScore:
	"""
	  A structured representation of the score supplied by the OMR tool
	"""
	def __init__(self, uri, json_data, config={}, editions=[]):
		"""
			Input: a validated JSON object. The method builds
			a representation based on the Python classes
		"""
		"""config = { "log_level": "INFO", "page_min":1, "system_min":1,
				"measure_min":1, "page_max": 1, "system_max":2,"measure_max": 999
				}
		"""
		print ("\n*** OMR score initialization\n")

		self.config = ParserConfig(config)
		self.config.print()		

		self.uri = uri 
		self.id = 1 #json_data["id"]
		self.score_image_url = "http://" # json_data["score_image_url"]
		#self.date = json_data["date"]
		self.json_data = json_data
		
		# The Score, obtained after a call to get_score
		self.score = None 
		
		# We will set initial signatures in case one is missing
		# on the initial measure
		self.initial_key_signature = score_notation.KeySignature()
		self.initial_time_signature = score_notation.TimeSignature()

		# We keep the list of key and time signatures occurrences,
		# indexed by the measure
		self.ks_per_measure = {}
		self.ts_per_measure = {}
		
		self.creator = annot_mod.Creator ("collabscore", 
										annot_mod.Creator.SOFTWARE_TYPE, 
										"collabscore")
		# We keep the post editions that apply to the MusicXML output
		self.post_editions = []
		# We add the editions received in parameter
		for edition in editions:
			if edition.name in Edition.POST_EDITION_CODES:
				self.post_editions.append (edition)
		
		# Decode the DMOS input as Python objects
		print ("\t*** Decode the OMR input\n")
		self.pages = []
		no_page = 1
		for json_page in self.json_data["pages"]:
			json_page["no_page"] = no_page # Bug in DMOS
			page = Page(json_page)							
			self.pages.append(page)
			no_page += 1
			
		# Produce the manifest of the score
		print ("\t*** Compute the score manifest\n")
		self.manifest = self.create_manifest()

		# Apply editions to correct the DMOS raw output and the manifest
		print ("\t*** Apply pre-editions\n")
		self.apply_pre_editions(editions)
				
		# Now the JSON is decoded and we assume that the structure
		# of the score, encoded in the manifest, is correct.
		# We run some additional tests (mostly on key and time signatures)
		# if necessary
		print ("\t*** Input decoded. Checking its consistency and fixing them\n")
		fix_editions = []
		current_measure_no = 1
		current_key_signature = None
		current_time_signature = None
		for page in self.pages:
			# Get the page from the manifest
			mnf_page = self.manifest.get_page(page.no_page)
			for system in page.systems:
				# Get the system from the manifest
				mnf_system = mnf_page.get_system(system.no_system_in_page)
				for measure in system.measures:
					# Check key signatures
					headers = Headers(Headers.KEYSIGN_TYPE, current_measure_no, mnf_system, measure.headers)
					measure.headers = headers.check_consistency ()
					if headers.signature is not None:
						# We found an occurrence. Check if a change occurred
						if current_key_signature is None or not headers.signature.equals(current_key_signature):
							self.ks_per_measure[current_measure_no] = headers.signature
							current_key_signature = headers.signature
					# Disabled, do better for transposing instruments
					#fix_editions += headers.fix_editions
					# Check time signatures
					headers = Headers(Headers.TIMESIGN_TYPE, current_measure_no, mnf_system, measure.headers)
					measure.headers  = headers.check_consistency ()
					#print (f"\nHeaders for measure {current_measure_no}")
					#for header in measure.headers:
					#	print (header) 
					if headers.signature is not None:
						# We found an occurrence 
						if current_time_signature is None or not headers.signature.equals(current_time_signature):
							self.ts_per_measure[current_measure_no] = headers.signature
							current_time_signature = headers.signature
					fix_editions += headers.fix_editions
					
					# Ok now check voices
					voices_to_remove = []
					for voice in measure.voices:
						dmos_voice = DmosVoice (current_measure_no, voice)
						if dmos_voice.is_empty():
							voices_to_remove.append(voice)
					for v in voices_to_remove:
							logger.warning (f"Remove an empty voice {voice.id} in measure {current_measure_no}")
							measure.voices.remove (v)
				
					current_measure_no += 1
					
					clefs_already_met = {}
					for voice in measure.voices:
						cleaned_items = []
						for item in voice.items:
							if item.clef_attr is not None:
								if not item.clef_attr.id in clefs_already_met.keys():
									clefs_already_met[item.clef_attr.id] = 1
									cleaned_items.append(item)
							else:
								cleaned_items.append(item)
						voice.items = cleaned_items
		# fix_editions =  self.check_and_fix_input()
		self.apply_pre_editions(fix_editions)

		# Show the list of signature changes
		#for meas_no, sign in self.ks_per_measure.items():
		#	print (f"Found a key signature change at measure {meas_no}: {sign}")
		#for meas_no, sign in self.ts_per_measure.items():
		#	print (f"Found a time signature change at measure {meas_no}: {sign}")

		# Determine the default signature
		if 1 not in  self.ks_per_measure.keys():
			# Whaouh, no key signature on the initial measure
			logger.warning (f"Missing key signature at the beginning of the score. Taking {self.initial_key_signature}")
		else: 
			self.initial_key_signature = self.ks_per_measure[1]
		if 1 not in  self.ts_per_measure.keys():
			# Whaouh, no time signature on the initial measure
			logger.warning (f"Missing time signature at the beginning of the score. Taking {self.initial_time_signature}")						
		else:
			self.initial_time_signature = self.ts_per_measure[1]

		print ("\n\t*** Initialization done. Ready to produce the score\n")

	def create_manifest(self):
		"""
		  The Manifest is a description of the source structure
		  in pages / systems / measures and staves
		"""
		manifest = Manifest(self.id, self.uri)
		for page in self.pages:
			# Create the manifest from the source
			src_page = source_mod.MnfPage(page.page_url, page.no_page, 0, 0,
										manifest)
			for system in page.systems:
				src_system = source_mod.MnfSystem(system.no_system_in_page, src_page,
												system.region.to_json())
				src_page.add_system(src_system)
				
				count_staff_per_part = {}
				for header in system.headers:
					src_staff = source_mod.MnfStaff(header.no_staff, src_system)
					src_system.add_staff(src_staff)
					if manifest.part_exists (header.id_part):
						# This part has already been met
						src_part = manifest.get_part (header.id_part)
					else:
						# It is a new part 
						src_part = source_mod.MnfPart(header.id_part, header.id_part, header.id_part) 
						manifest.add_part(src_part)
					
					# Did we get the name of the part ?
					if header.part_name is not None and header.part_name != "":
						src_part.name = header.part_name
						
					# Count the number of staves for the part
					if header.id_part in count_staff_per_part.keys():
						count_staff_per_part[header.id_part] += 1
					else:
						count_staff_per_part[header.id_part] = 1
						
					src_staff.add_part(header.id_part)
					
				for measure in system.measures:
					src_measure = source_mod.MnfMeasure(measure.no_measure_in_score, 
													  measure.no_measure_in_system,
													  "", # So far we do not know the MEI id
													  src_system,
														measure.region.to_json())
					src_system.add_measure(src_measure)
			manifest.add_page(src_page)
		
		# Now we create the groups to detect parts that extend over several staves
		manifest.create_groups()
		# Clean pages URL and find the first page of music
		manifest.clean_pages_url()
		
		#
		# A QUOI CA SERT ???
		#manifest.get_first_music_page()
		return manifest
		
	def apply_pre_editions(self, editions):
		"""
		  Most of the editions are applied to the DMOS input, before
		  producing the score
		"""
		# Create a double dictionary indexed on the edition target + element id, referring
		# to the editions that must be applied at run time
		replacements = {Edition.REPLACE_CLEF: {}, 
					    Edition.REPLACE_KEYSIGN: {}, 
					    Edition.REPLACE_TIMESIGN: {},
					    Edition.COMMENT_ELEMENT: {},
					    Edition.REPLACE_MUSIC_ELEMENT: {}}
		# Dictionary of objects to remove
		removals = {}

		# We add the editions received in parameter
		for edition in editions:
			if edition.name in Edition.PARSE_TIME_EDITION_CODES:
				# One edition can apply to many graphical objects (eg keys/tsign).
				# The ids of the graphical object are separated by ID_SEPARATOR
				ids = edition.target.split (constants_mod.ID_SEPARATOR)
				if edition.name == Edition.REMOVE_OBJECT:
					for id in ids:
						edition.target = id
						logger.warning (f"Add edition {edition} for object {id}")
						removals[edition.target] = edition.params
				else:
					for id in ids:
						edition.target = id
						logger.warning (f"Add edition {edition} for object {id}")
						replacements[edition.name][id] = edition.params
			elif edition.name in Edition.PRE_EDITION_CODES:
				# Pre editions  concern pages  and staff layout are applied the manifest
				edition.apply_to(self)
		
		# Finally we scan the structure decoded from DMOS, and apply editions
		for page in self.pages:
			#print (f"Apply editions to page {page}")
			for system in page.systems:
				#print (f"\tApply editions to system {system}")
				for measure in system.measures: 
					#print (f"\t\tApply editions to measure {measure}")
					for header in measure.headers:
						if header.clef is not None:
							if header.clef.id in replacements[Edition.REPLACE_CLEF].keys():
								replacement = replacements[Edition.REPLACE_CLEF][header.clef.id]
								header.clef.overwrite (replacement)
								logger.info (f"Clef {header.clef.id} has been replaced")
							if header.clef.id in removals:
								logger.info (f"Clef {header.clef.id} has been removed")
								header.clef = None

						if header.time_signature is not None:
							if header.time_signature.id in replacements[Edition.REPLACE_TIMESIGN].keys():
								replacement = replacements[Edition.REPLACE_TIMESIGN][header.time_signature.id]
								header.time_signature.overwrite (replacement)
							if header.time_signature.id in removals:
								logger.info (f"Time signature {header.time_signature.id} has been removed")			
								header.time_signature = None
								
						if header.key_signature is not None:
							if header.key_signature.id in replacements[Edition.REPLACE_KEYSIGN].keys():
								replacement = replacements[Edition.REPLACE_KEYSIGN][header.key_signature.id]
								header.key_signature.overwrite (replacement)
							if  header.key_signature.id in removals:
								logger.info (f"Key signature {header.key_signature.id} has been removed")
								header.key_signature = None

					for voice  in measure.voices: 
						for item in voice.items: 
							if item.note_attr is not None or item.rest_attr is not None:
								if item.note_attr is not None:
									heads = item.note_attr.heads
								else:
									heads = item.rest_attr.heads
								for head in heads:
									if head.id in replacements[Edition.REPLACE_MUSIC_ELEMENT].keys():
										head.overwrite (replacements[Edition.REPLACE_MUSIC_ELEMENT][head.id])
										item.duration.overwrite (replacements[Edition.REPLACE_MUSIC_ELEMENT][head.id])
										if "switch" in replacements[Edition.REPLACE_MUSIC_ELEMENT][head.id]:
											if item.note_attr is not None:
												#print (f"Note {head.id} becomes a rest")
												# A note becomes a rest
												item.rest_attr = item.note_attr
												item.note_attr = None
											else:
												#print (f"Rest {head.id} becomes a note")
												# A rest becomes a note. We give an impossible height, that
												# will be adjusted based on the Clef (not known yet)
												head.height = 999
												item.note_attr = item.rest_attr
												item.rest_attr = None
												
									if head.id in removals:
										logger.info (f"Note head {head.id}  is removed")
										heads.remove(head)
							if item.clef_attr is not None:
								#This is a clef change 
								if item.clef_attr.id in replacements[Edition.REPLACE_CLEF].keys():
									logger.info (f"Voice clef {item.clef_attr.id} has been replaced")
									replace = replacements[Edition.REPLACE_CLEF][item.clef_attr.id]
									item.clef_attr.overwrite (replace)
								if item.clef_attr.id in removals:
									logger.info (f"Voice clef {item.clef_attr.id} has been removed")
									voice.items.remove(item)
	
	def produce_annotations (self, score):
		"""
		  Scan the DMOS structure and produce regions and errors annotations
		"""
		# We keep the measure id along the way
		current_measure_no = 0
		for page in self.pages:
			# Get the page from the manifest
			mnf_page = self.manifest.get_page(page.no_page)
			for system in page.systems:
				# Get the system from the manifest
				mnf_system = mnf_page.get_system(system.no_system_in_page)
				# Annotate the region of the whole system
				annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, f"P{page.no_page}-S{system.no_system_in_page}", 
							page.page_url, system.region.string_xyhw(), 
							constants_mod.IREGION_SYSTEM_CONCEPT)
				score.add_annotation (annotation)

				for staff_header in system.headers:
					if staff_header.region is not None:
						# Record the region of the staff in the system
						annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
									self.creator, self.uri, f"P{page.no_page}-S{system.no_system_in_page}-{staff_header.no_staff}", 
									page.page_url, staff_header.region.string_xyhw(), 
									constants_mod.IREGION_STAFF_CONCEPT)
						score.add_annotation (annotation)

				for measure in system.measures: 
					current_measure_no += 1
					# Annotate this measure
					annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, f"m{current_measure_no}", 
							page.page_url, measure.region.string_xyhw(), 
							constants_mod.IREGION_MEASURE_CONCEPT)
					score.add_annotation (annotation)

					for header in measure.headers:
						mnf_staff = mnf_system.get_staff(header.no_staff)
						id_part = mnf_staff.get_part_id()
						if header.region is not None:
							# Record the region of the measure for the current staff
							annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
									self.creator, self.uri, score_model.Measure.make_measure_id(id_part, current_measure_no), 
									page.page_url, header.region.string_xyhw(), 
									constants_mod.IREGION_MEASURE_STAFF_CONCEPT)
							score.add_annotation (annotation)
						if header.clef is not None:
							for error in header.clef.errors:
								score.add_annotation (annot_mod.Annotation.create_from_error (
										self.creator, self.uri, header.clef.id, error.message))
						if header.time_signature is not None:
							for error in header.time_signature.errors:
								score.add_annotation (annot_mod.Annotation.create_from_error (
										self.creator, self.uri, header.time_signature.id, error.message))
						if header.key_signature is not None:
							for error in header.key_signature.errors:
								score.add_annotation (annot_mod.Annotation.create_from_error (
										self.creator, self.uri, header.key_signature.id, error.message))
						
					for voice  in measure.voices: 
						for voice_item in voice.items: 
							if voice_item.note_attr is not None or voice_item.rest_attr is not None:
								if voice_item.note_attr  is not None:
									heads = voice_item.note_attr.heads
								else:
									heads = voice_item.rest_attr.heads
								for head in heads:
									if head.head_symbol.region is not None:
										annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
											self.creator, self.uri, head.id, 
											page.page_url, head.head_symbol.region.string_xyhw(), 
											constants_mod.IREGION_NOTE_CONCEPT)
										score.add_annotation (annotation)
									# Did we met errors at the voice item level ?
									for error in voice_item.errors:
										score.add_annotation (annot_mod.Annotation.create_from_error (
											self.creator, self.uri, head.id, error.message))
									# Clear the errors to avoid attaching them to each head
									voice_item.errors = []
									# Did we met errors at the head level ?
									for error in voice_item.errors:
										score.add_annotation (annot_mod.Annotation.create_from_error (
											self.creator, self.uri, head.id, error.message))
									#else:
									#	score_model.logger.warning (f"No region for an event. Probably a non visible rest")
							elif voice_item.clef_attr is not None:
								clef_region = voice_item.clef_attr.symbol.region
								#This is a clef change 
								if clef_region is not None:
									annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
											self.creator, self.uri, voice_item.clef_attr.id, 
											self.score_image_url, clef_region.string_xyhw(), 
											constants_mod.IREGION_SYMBOL_CONCEPT)
									score.add_annotation (annotation)
								for error in voice_item.clef_attr.errors:
									score.add_annotation (annot_mod.Annotation.create_from_error (
											self.creator, self.uri, voice_item.clef_attr.id, error.message))

				
	def get_score(self):
		'''
			Builds a score (instance of our score model) from the Omerized document
		'''		
		
		print ("\n*** Create the score from the OMR input\n")
		
		# Create an OMR score (with layout)
		if self.score != None:
			# print ("The score has already been computed. We return the version in cache")
			return self.score # Returning the score in cache
		
		# The score has not yet been computed
		score = self.initialize_score()
		
		# Produce annotations that can be determined now
		print ("Producing annotations")
		self.produce_annotations(score)
		
		logger.info (f"")
		logger.info (f"== End of score structure creation. Scanning pages ===")

		# Main scan: we fill the parts with measures
		current_measure_no = 0
		
		for page in self.pages:
			if not self.config.in_range (page.no_page):
				continue
			
			logger.info (f"")
			logger.info (f'** Process page {page.no_page}')

			# Get the page from the manifest
			mnf_page = self.manifest.get_page(page.no_page)
			
			#print (f"Processing page {page.no_page}")
			if current_measure_no > 0:
				# We are not on the first page
				page_begins = True
			else:
				page_begins = False
			for system in page.systems:
				system_begins = True
				if not self.config.in_range (page.no_page, system.no_system_in_page):
					continue

				logger.info (f"")
				logger.info (f'*** Process system {system.no_system_in_page}')

				# Get the system from the manifest
				mnf_system = mnf_page.get_system(system.no_system_in_page)

				# Now, for the current system, we know the parts and the staves for 
				# each part, initialized with their time signatures
				# We scan the measures. DMOS gives us a measure for all the parts of the system. 
				# We add one measure to each part.
				for measure in system.measures:
					current_measure_no += 1
					if not self.config.in_range (page.no_page, system.no_system_in_page, measure.no_measure_in_system):
						logger.info (f'Skipping measure {current_measure_no}')
						continue
				
					logger.info (f"")
					logger.info (f'***** Process measure {current_measure_no}, to be inserted at position {score.duration().quarterLength}')

					# Accidentals are reset at the beginning of measures
					score.reset_accidentals()
					
					# Create a new measure for each part
					for part in score.get_parts():
						logger.info (f"Adding measure {current_measure_no} to part {part.id}")
						# We initialize the measure signatures with the current defaults
						default_ks = None
						if current_measure_no in self.ks_per_measure.keys():
							default_ks = self.ks_per_measure[current_measure_no]
						default_ts =None
						if current_measure_no in self.ts_per_measure.keys():
							default_ts = self.ts_per_measure[current_measure_no]
						part.add_measure (current_measure_no, default_ts, default_ks)
						part.reset_voice_counter()

						# Adding page and system breaks
						if 	page_begins:
							part.add_page_break()
							page_begins = False
							system_begins = False
						elif system_begins and system.no_system_in_page > 1:
							## Add a system break
							part.add_system_break()
							system_begins = False

					# Measure headers (DMOS) tells us, for each staff, if 
					# one starts with a change of clef or meter
					new_time_signature = None
					for header in measure.headers:
						# Identify the part, staff and measure, from the staff id
						mnf_staff = mnf_system.get_staff(header.no_staff)
						id_part = mnf_staff.get_part_id()
						part = score.get_part (id_part)
						measure_for_part = part.get_measure_from_staff(mnf_staff.number_in_part)				

						if header.clef is not None:
							clef_staff = header.clef.get_notation_clef()
							clef_position = part.get_duration()
							clef_changed = part.set_current_clef (clef_staff, mnf_staff.number_in_part, clef_position)
							# Annotate this symbol
							if header.clef.id == None:
								logger.error (f"Null XML ID for a clef. Ignored.")
							else:
								if clef_changed:
									logger.info (f"Clef {clef_staff} changed on staff {header.no_staff} with id {clef_staff.id} at measure {current_measure_no}, position {clef_position}")
									annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
										self.creator, self.uri, header.clef.id, 
										page.page_url, header.clef.symbol.region.string_xyhw(), constants_mod.IREGION_SYMBOL_CONCEPT)
									score.add_annotation (annotation)
								else:
									logger.info (f"Clef {clef_staff} found on staff {header.no_staff} without change. Ignored.")									

						if header.time_signature is not None:
							logger.info (f'Found time signature  {header.time_signature} on staff {header.no_staff} at measure {current_measure_no}')
							new_time_signature = header.time_signature.get_notation_object()
							# We assign the TS specifically to the current parts: the id is preserved
							changed_ts = part.set_current_time_signature (new_time_signature, mnf_staff.number_in_part)			
							if not changed_ts:
								logger.info (f'Time signature  {new_time_signature} with id {new_time_signature.id} found on staff {header.no_staff} at measure {current_measure_no} without change. Ignored.')
								
							# Annotate the key with its region
							if header.time_signature.region is not None and header.time_signature.id is not None:
								if changed_ts:
									logger.info (f'New time signature  {new_time_signature} with id {new_time_signature.id} found on staff {header.no_staff} at measure {current_measure_no}')
									annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
										self.creator, self.uri, header.time_signature.id, 
										page.page_url, header.time_signature.region.string_xyhw(), constants_mod.IREGION_SYMBOL_CONCEPT)
									score.add_annotation (annotation)
							#else:
							#	logger.warning (f"Null region or XML ID for a time signature. No annotation produced")

						if header.key_signature is not None:
							key_sign = header.key_signature.get_notation_object()
							# The key signature impacts all subsequent events on the staff
							changed_key = part.set_current_key_signature (key_sign, mnf_staff.number_in_part)
							# We will display the key signature at the beginning
							# of the current measure
							if changed_key:
								logger.info (f'New key signature {key_sign} found on staff {header.no_staff} at measure {current_measure_no}')
								if header.key_signature.region is not None and header.key_signature.id is not  None:
									annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
										self.creator, self.uri, header.key_signature.id, 
										page.page_url, header.key_signature.region.string_xyhw(), constants_mod.IREGION_SYMBOL_CONCEPT)
									score.add_annotation (annotation)
								else:
									logger.error (f"Null region or XML ID for a key signature. Ignored")
							else:
								logger.info (f'Key signature {key_sign} found on staff {header.no_staff} at measure {current_measure_no} without change. Ignored.')
					
					# Now we scan the voices
					
					# Voices are numbered from 1 for 
					for voice in measure.voices:
						current_part = score.get_part(voice.id_part)
						i_voice_for_part = current_part.new_voice_counter()
						logger.info (f"")
						logger.info (f'Process voice {voice.id} in part {current_part.id}')
						
						# Reset the event counter
						score_events.Event.reset_counter(
							f'F{page.no_page}{voice.id_part}M{current_measure_no}{voice.id}')

						# Create the voice (no more voice.id)
						voice_part = voice_model.Voice(part=current_part,voice_id=str(i_voice_for_part))
						voice_part.absolute_position = measure_for_part.absolute_position
						# We disable automatic beaming
						voice_part.automatic_beaming = False

						# Now we add events to the voice						
						current_beam = None						
						previous_event = None
						for item in voice.items:
							# Duration exception: in case of "whole" note, depends 
							# on the time signature
							if item.duration is not None and item.duration.whole:
								# A la blanche (4) ou autre (3/1, 3/2, 6/8, etc)
								item.duration.numer =  4* current_part.get_current_time_signature().numer 
								item.duration.denom = current_part.get_current_time_signature().denom
							# Decode the event
							(event, type_event) = self.decode_event(mnf_system, voice_part, item) 
							
							if event is None:
								# We met an event without head: probably removed
								logger.warning ("Found a None event. Probably no head.... ignored")
								continue
							
							# Manage beams
							if current_beam != item.beam_id:
								if current_beam != None:
									# The previous event was the end of the beam
									#print (f"Stop beam {current_beam}")
									previous_event.stop_beam(current_beam)
								if item.beam_id != None:
									#print (f"Start beam {item.beam_id}")
									event.start_beam(item.beam_id)
								current_beam =  item.beam_id
								
							previous_event = event
							
							if type_event == "event":
								if event.get_duration() == 0.:
									logger.error (f"Null duration for event. Ignored")
								else:
									## Add decorations first (pos. of the nevent)
									for decoration in event.decorations:
										voice_part.append_decoration(decoration)
									voice_part.append_event(event)
									# Note: color 0 is never used
									event.set_color(int(voice_part.id) - 1)
							elif type_event == "clef":
								# The staff id is in the voice item
								id_staff = item.no_staff_clef
								mnf_staff = mnf_system.get_staff(id_staff)
								clef_position = measure_for_part.absolute_position + voice_part.get_duration()
								# We found a clef change
								logger.info (f"Clef {event} found on staff {id_staff} with id {event.id} at position {clef_position}")
								current_part.set_current_clef (event, mnf_staff.number_in_part, clef_position)
							else:
								logger.error (f'Unknown event type {type_event} for voice {voice.id}')
										
						# End of items for this measure. Close any pending beam
						if current_beam != None:
							#print (f"Stop beam {current_beam}")
							previous_event.stop_beam(current_beam)
							current_beam =  None
													
						# Add the voice to the measure of the relevant part
						if voice_part.nb_events() > 0:
							# This functions computes the main staff of the voice
							current_part.add_measure_voice (voice_part)
							
							# Searching for events outside the main staff
							if current_part.part_type == score_model.Part.GROUP_PART:
								for event in voice_part.events:
									if event.is_note() or event.is_rest():
										move = self.move_to_correct_staff(event, voice_part.main_staff)
										if move is not None:
											self.post_editions.append(move)
									elif event.is_chord():
										for note in event.notes:
											move = self.move_to_correct_staff(note, voice_part.main_staff)
											if move is not None:
												self.post_editions.append(move)
						else:
							logger.warning (f"Found an empty voice {voice_part.id} in measure {measure_for_part.id} of part {current_part.id}. Ignored")
											
					# Checking consistency of signatures
					logger.info("")
					logger.info("Checking  signatures for the current measure")
					logger.info("")
					# In principle the input has been cleaned
					#score.check_signatures()

		# Aggregate voices at the part level
		logger.info("")
		logger.info("Create part voices from measure voices")
		logger.info("")
		score.aggregate_voices_from_measures()
		# Now clean the voice of possible inconsistencies. For
		# instance ties that to not make sense
		score.clean_voices() 

		# Time to check the consistency of the measure
		logger.info("")
		logger.info("Checking consistency of measures")
		logger.info("")
		list_removals = score.check_measure_consistency()			

		for removal in list_removals:
			# Adding removed events to the post editions they
			# must be reinserted in the XML file
			if removal.target is not None:
				self.post_editions.append( editions_mod.Edition (editions_mod.Edition.APPEND_OBJECTS, 
																removal.target.id, {"events": removal.list_events}))
			else:
				logger.warning (f"An element over measure limit must be removed but has no id. Ignored")			
	
		# Remove in the XML file the pseudo-beam
		self.post_editions.append( editions_mod.Edition (editions_mod.Edition.CLEAN_BEAM, "score"))

		self.score = score 			
		return self.score

	def decode_event(self, mnf_system, voice, voice_item):
		'''
			Produce an event (from our score model) and its region by decoding the OMR input
		'''
		
		if voice_item.duration is not None:	
			# Duration of the event (note, rest or chord): the DMOS encoding is 1 from whole note, 2 for half, etc.
			# Our encoding (music21) is 1 for quarter note. Hence the computation
			duration = score_events.Duration(voice_item.duration.numer * voice_item.tuplet_info.num_base, 
										voice_item.duration.denom * voice_item.tuplet_info.num)
		else:
			duration = None # Must be a clef
		if voice_item.note_attr is not None:
			# It can be a note or a chord
			events = []
			for head in voice_item.note_attr.heads:
				id_staff = StaffHeader.make_id_staff(head.no_staff) # Will be used as the chord staff.
				mnf_staff = mnf_system.get_staff(id_staff)
				
				# Get the sub-part where the event is positioned. Seen as a staff
				staff = voice.part.get_part_staff(mnf_staff.number_in_part)
				event_position = voice.absolute_position + voice.get_duration()
				current_clef = staff.get_clef_at_pos(event_position)
				# Special: if a rest has been changed in note, we do not know
				# the height which has been set to 999 during replacement.
				if head.height == 999:
					head.height = current_clef.default_height
				# The head position gives the position of the note on the staff
				(pitch_class, octave)  = current_clef.decode_pitch (head.height)
			
				# Did we just met an accidental?
				if (head.alter != score_events.Note.ALTER_NONE):
					logger.info (f'Accidental {head.alter} met on staff {staff.id}')
					staff.add_accidental (pitch_class, head.alter)
					alter = head.alter
				else:
					if staff.accidentals[pitch_class] != score_events.Note.ALTER_NONE:
						# accidental met on staff
						alter = staff.accidentals[pitch_class]
					else: 
						alter = voice.part.get_current_key_signature().accidental_by_step(pitch_class)
			
				note = score_events.Note(pitch_class, octave, duration, alter, 
											mnf_staff.number_in_part, 
											stem_direction=voice_item.direction,
											note_type=voice_item.duration.note_type,
											id=head.id,
											voice=voice)
				
				# Check ties
				if head.tied and head.tied=="forward":
					#print (f"Tied note {note} start with id {head.id_tie}")
					note.start_tie(head.id_tie)
				if head.tied and head.tied=="backward":
					#print (f"Tied note {note} ends with id {head.id_tie}")
					note.stop_tie(head.id_tie)
				
				# Add articulations and dynamics
				self.add_expression_to_event(events, note, head.articulations)
				events.append(note)
				
			if len(events) == 1:
				# A single note
				event = events[0]
				logger.info (f'Adding note {event.pitch_class}{event.octave}-{event.alter}, duration {event.duration.get_value()} to staff {id_staff} with current clef {current_clef}.')
				# Is there a syllable ?
				i_verse = 1
				for syl in voice_item.note_attr.syllables:
					event.add_syllable(syl["text"],nb=i_verse,dashed=syl["followed_by_dash"])
					i_verse += 1
			elif len(events) > 1:
				# A chord
				logger.info (f'Adding a chord with {len(events)} notes.')
				for event in events:
					logger.info (f'\tNote {event.id} {event.pitch_class}{event.octave}-{event.alter}, duration {event.duration.get_value()} to staff {id_staff} with current clef {current_clef}.')
					last_note_id = event.id
				# MusicXML does not keep the chord id, so we identify it by the last note id to be able to find it in the XML encoding
				event = score_events.Chord (duration, mnf_staff.number_in_part, events, id=last_note_id, voice=voice)
				self.add_expression_to_event(events, event, head.articulations)
			else:
				# Case of an event with no head: probably a removed event
				event = None
		elif voice_item.rest_attr is not None:
			# It is a rest
			# Case of an event with no head: probably a removed event
			event = None
			for head in voice_item.rest_attr.heads:
				id_staff = StaffHeader.make_id_staff(head.no_staff) # Will be used as the chord staff.
				mnf_staff = mnf_system.get_staff(id_staff)
				event = score_events.Rest(duration, mnf_staff.number_in_part, id=head.id, voice=voice)
				event.set_visibility(voice_item.rest_attr.visible)
				logger.info (f'Adding rest {event.id} with duration {duration.get_value()} to staff {id_staff}.')
		elif voice_item.clef_attr is not None:
			#This is a clef change 
			event = voice_item.clef_attr.get_notation_clef()
			return (event, "clef")
		else:
			logger.error ("A voice event with unknown type has been met")
			raise CScoreParserError ("A voice event with unknown type has been met")
		
		return (event, "event")

	def initialize_score(self):
		"""
		  This function initializes a music score with its parts 
		"""

		score =  score_model.Score(use_layout=False)
		score.set_initial_time_signature(self.initial_time_signature)
		logger.info (f"Initial key signature set to {self.initial_time_signature}")
		score.set_initial_key_signature(self.initial_key_signature)
		logger.info (f"Initial key signature set to {self.initial_key_signature}")

		# The manifest tells us the parts of the score: we create them
		for src_part in self.manifest.get_parts():
			# Parts are identified by the part id + staff id. In general
			# there is only on staff per part
			if not self.manifest.is_a_part_group(src_part.id):
				id_part_staff = score_model.Part.make_part_id(src_part.id)
				part = score_model.Part(id_part=id_part_staff, name=src_part.name, 
												abbreviation=src_part.abbreviation)
				
				part.set_instrument (src_part.name,src_part.abbreviation)
				score.add_part(part)			
				logger.info (f"Add a single-staff part {id_part_staff}")
			else:
				# It is a part group. Create one PartStaff for each staff of the part 
				staff_group = []
				i_staff = 0
				for staff in self.manifest.groups[src_part.id]:
					id_part_staff = score_model.Part.make_part_id(src_part.id, i_staff)
					i_staff+= 1
					part_staff = score_model.Part(id_part=id_part_staff, name=src_part.name, 
												abbreviation=src_part.abbreviation,
												part_type=score_model.Part.STAFF_PART, 
												no_staff=i_staff)
					
					logger.info (f"Add a staff part {id_part_staff} in a part group")
					staff_group.append(part_staff)
					score.add_part(part_staff)
				# + a Staff group for the global part
				part_group = score_model.Part(id_part=src_part.id, name=src_part.name, 
												abbreviation=src_part.abbreviation,
												part_type=score_model.Part.GROUP_PART, 
												group=staff_group)
				part_group.set_instrument (src_part.name, src_part.abbreviation)
				logger.info (f"Add a part group {src_part.id} with {i_staff} staff-parts")
				score.add_part(part_group)
		

		return score

	def move_to_correct_staff(self, note, main_staff):
		# Register an edition to move a note to its correct staff
		if note.no_staff != main_staff:
			if note.no_staff < main_staff:
				direction = "up"
			else:
				direction = "down"
			logger.info  (f"Moving event {note.get_code()} direction {direction} ")
			move = editions_mod.Edition (editions_mod.Edition.MOVE_OBJECT_TO_STAFF,
										 note.id, 
										{"staff_no": note.no_staff,
										"direction": direction})
			return move
		else:
			return None

	def add_expression_to_event(self, events, event, articulations):
		for json_art in articulations:
			if json_art["label"] in ARTICULATIONS_LIST:
				articulation = score_events.Articulation(json_art["placement"], json_art["label"])
				event.add_articulation(articulation)
			elif json_art["label"] in EXPRESSIONS_LIST:
				expression = score_events.Expression(json_art["placement"], json_art["label"])
				event.add_expression(expression)
			elif json_art["label"] in DYNAMICS_LIST:
				dynamic = score_events.Dynamics(json_art["placement"], json_art["label"])
				# A dynamic is inserted in the music flow
				event.add_decoration(dynamic)

	def write_as_musicxml(self, out_file):
		print ("\nCreate the score from JSON input")
		score = self.get_score()
		
		print (f"\nWriting as MusicXML in {out_file}")
		score.write_as_musicxml (out_file)
		
		print ("\nApplying post-editions to the MusicXML file\n")
		Edition.apply_editions_to_file (self.post_editions, out_file)
		print ("\nPost-editions done\n")

			
	def write_as_mei(self, mxml_file, out_file):
		self.get_score().write_as_mei (mxml_file, out_file)

	def write_as_pickle(self, filename):
		self.get_score().write_as_pickle (filename)

class Point:
	"""
		A geometric point
	"""
	
	def __init__(self,json_point):
		self.x = json_point[0]
		self.y = json_point[1]

	def __str__(self):
		return f'(P{self.x},{self.y})'

	def to_json(self):
		return [self.x, self.y]
	
class Segment:
	"""
		A segment  described by its two endpoints
	"""
	
	def __init__(self,json_segment):
		self.ll = Point (json_segment[0])
		self.ur = Point (json_segment[1])

	def __str__(self):
		return f'(Segment({self.ll},{self.ur})'

class Region:
	"""
		A polygon described by its contour
	"""
	
	def __init__(self,json_region):
		self.contour = []
		for json_point in json_region:
			self.contour.append(Point(json_point))

	def __str__(self):
		
		str_repr =""
		for point in self.contour:
			str_repr += str(point)

		return f'({str_repr})'
		
		# Pour encoder plutôt en JSON
		# return json.dumps(self.to_json())
	
	def to_json(self):
		res = []
		for pt in self.contour:
			res.append(pt.to_json())
		return res
	
	def string_xyhw(self):
		return f'{self}'

class Rectangle:
	"""
		A specific region. Maybe not useful
	"""
	
	def __init__(self,json_rectangle):
		self.x = json_rectangle[0]
		self.y = json_rectangle[1]
		self.height = json_rectangle[2]
		self.width = json_rectangle[3]

	def __str__(self):
		return f'({self.x},{self.y},{self.height},{self.width})'
	
	def string_xyhw(self):
		return f'{self.x},{self.y},{self.height},{self.width}'

class Symbol:
	"""
		An uninterpreted symbol (e.g, a Clef)
	"""
	def __init__(self, json_symbol):
		self.label = json_symbol["label"]
		
		if "region" in json_symbol:
			self.region = Region(json_symbol["region"])
		else: 
			self.region = None

	def __str__(self):
		return f'({self.label},{self.region})'

class Page:
	"""
		An page containing systems
	"""
	
	def __init__(self, json_page):
		if "page_url" in json_page:
			self.page_url = json_page["page_url"]
		else: 
			self.page_url = "Unspecified page URL"

		self.no_page = json_page["no_page"]
		self.systems=[]
		
		i_system=1
		for json_system in json_page["systems"]:
			self.systems.append(System(json_system))

	def __str__(self):
		return f"{self.no_page}"
	
class System:
	"""
		A system containing measures
	"""
	
	def __init__(self, json_system):
		self.id = json_system["id"]
		self.no_system_in_page = self.id
		self.no_system_in_score = None
		self.region = Region (json_system["region"])
		self.headers = []
		for json_header in json_system["headers"]:
			self.headers.append(StaffHeader(json_header))
		self.measures = []
		i_measure_in_system = 1
		for json_measure in json_system["measures"]:
			self.measures.append(Measure(json_measure, i_measure_in_system))
			i_measure_in_system += 1

	def __str__(self):
		return f"{self.no_system_in_page} in page -- {self.no_system_in_score} in score"

class Measure:
	"""
		An measure containing voices
	"""
	
	def __init__(self, json_measure, i_measure_in_system):
		self.no_measure_in_system = i_measure_in_system
		self.no_measure_in_score = None

		if "region" in json_measure:
			self.region = Region (json_measure["region"])
		self.headers =[]
		for json_header in json_measure["headers"]:
			self.headers.append(MeasureHeader(json_header))
		self.voices =[]
		for json_voice in json_measure["voices"]:
			self.voices.append(Voice(json_voice))

	def __str__(self):
		return f"{self.no_measure_in_system} in system - {self.no_measure_in_score} in score"

class Voice:
	"""
		An voice containing voice elements
	"""
	
	def __init__(self, json_voice):
		self.id = json_voice["id"]
		self.id_part =  StaffHeader.make_id_part ( json_voice["id_part"])
		# Obsolete, since a voice can spread several parts
		#self.id_staff =  StaffHeader.make_id_staff ( json_voice["id_part"])
		
		self.items = []
		for json_item in json_voice["elements"]:
			self.items.append(VoiceItem (json_item))

	def __str__(self):
		return f"{self.id}"
			
		
class VoiceItem:
	"""
		A voice item
	"""
	
	def __init__(self, json_voice_item):
		self.note_attr = None
		self.rest_attr = None
		self.clef_attr = None
		self.no_staff_clef = None
		self.beam_id = None
		self.tuplet_info  =  TupletInfo ({"num":1, "numbase": 1})
		self.numbase = 1
		
		if "duration" in json_voice_item:
			self.duration = Duration (json_voice_item["duration"])
		else:
			# Must be a clef
			if not ("att_clef" in json_voice_item):
				raise CScoreParserError ("A voice item is not a clef and does not have a duration")
			self.duration = None
		if "no_group" in json_voice_item:
			no_group = json_voice_item["no_group"]
			# Assume that 0 is a no-value
			if no_group > 0:
				self.beam_id = json_voice_item["no_group"]
				
		if "tuplet_info" in json_voice_item:
			self.tuplet_info = TupletInfo (json_voice_item["tuplet_info"])

		self.direction = None
		if "direction" in json_voice_item:
			self.direction = json_voice_item["direction"]
			self.type = "Direction"
		
		# Read the errors, before assigning them to he proper type
		errors = []
		if "errors" in json_voice_item:
			for json_error in json_voice_item["errors"]:
				errors.append(Error (json_error))

		if "att_note" in json_voice_item:
			self.note_attr = NoteAttr (json_voice_item["att_note"])
			self.type= "Note or chord"
			self.note_attr.errors = errors
		if "att_rest" in json_voice_item:
			# NB: using the same type for note heads and rest heads
			self.rest_attr = NoteAttr (json_voice_item["att_rest"])
			self.rest_attr.errors = errors
			self.type="Note"
		if "att_clef" in json_voice_item:
			self.clef_attr  = Clef (json_voice_item["att_clef"])
			self.no_staff_clef = StaffHeader.make_id_staff(json_voice_item["att_clef"]["no_staff"])
			self.clef_attr.errors = errors
			self.type="Clef"
		self.errors = []

	def __str__(self):
		return f'({self.type}, dur. ({self.duration.numer}/{self.duration.denom})'

class NoteAttr:
	"""
		Note attributes
	"""
	
	def __init__(self, json_note_attr):
		
		self.nb_heads = json_note_attr["nb_heads"]
		self.heads = []
		self.visible = True
		self.syllables = []
		if "visible" in json_note_attr:
			self.visible = json_note_attr["visible"]
		if "syllable" in json_note_attr:
			self.syllables.append(json_note_attr["syllable"])
		if "verses" in json_note_attr:
			for syl in json_note_attr["verses"]:
				self.syllables.append(syl)
		for json_head in json_note_attr["heads"]:
			note = Note (json_head)
			
			# Get the articulation symbol attached to the note
			if "articulations_top" in json_note_attr.keys():
				for json_art in json_note_attr["articulations_top"]:
					note.add_articulation (ABOVE, json_art)
			if "articulations_bottom" in json_note_attr.keys():
				for json_art in json_note_attr["articulations_bottom"]:
					note.add_articulation (BELOW, json_art)
			self.heads.append(note)

##############

class Note:
	"""
		Representation of a Note
	"""
	
	def __init__(self, json_note):
		if "id" in json_note:
			self.id =  json_note["id"]
		else:
			self.id =  None
		self.tied  = "none"
		self.id_tie = 0
		self.alter = score_events.Note.ALTER_NONE
		
		# A request can be made to change an alteration. Default 0
		#self.alter_change = 0
		
		self.head_symbol =  Symbol (json_note["head_symbol"])
		self.no_staff  = json_note["no_staff"]
		self.height  = json_note["height"]
		
		self.articulations = []
		if "alter" in json_note:
			alter_label = json_note["alter"]["label"]
			if alter_label == FLAT_SYMBOL:
				self.alter = score_events.Note.ALTER_FLAT
			elif alter_label == DFLAT_SYMBOL:
				self.alter = score_events.Note.ALTER_DOUBLE_FLAT
			elif alter_label  == SHARP_SYMBOL:
				self.alter = score_events.Note.ALTER_SHARP
			elif alter_label  == DSHARP_SYMBOL:
				self.alter = score_events.Note.ALTER_DOUBLE_SHARP
			elif alter_label  == NATURAL_SYMBOL:
				self.alter = score_events.Note.ALTER_NATURAL
			else:  
				logger.warning (f'Unrecognized alter code {alter_label}. Replaced by None')

		if "tied" in json_note:
			self.tied = json_note["tied"]
		if "id_tie" in json_note:
			self.id_tie  = json_note["id_tie"]

	def add_articulation(self, placement, json_art):
		self.articulations.append({"placement": placement, "label": json_art["label"]})

	def overwrite (self, edition):
		# Apply an edition to the note head
		if "pitch_change" in edition:
			#print (f"Head pitch must be moved {edition['pitch_change']} steps")
			self.height += edition['pitch_change']
		if "alter" in edition:
			#print (f"Head pitch alteration must be  {edition['alter']}")
			alter = edition['alter']
			if alter == -1:
				self.alter = score_events.Note.ALTER_FLAT
			elif alter == -2:
				self.alter = score_events.Note.ALTER_DOUBLE_FLAT
			elif alter == 1:
				self.alter = score_events.Note.ALTER_SHARP
			elif alter == 2:
				self.alter = score_events.Note.ALTER_DOUBLE_SHARP
			elif alter == 0:
				self.alter = score_events.Note.ALTER_NATURAL

class Clef:
	"""
		Representation of a clef
	"""
	
	def __init__(self, json_clef):
		if "id" in json_clef:
			self.id  = json_clef["id"]
		else:
			self.id = None

		self.symbol =  Symbol (json_clef["symbol"])
		self.height  = json_clef["height"]
		self.octave_change = 0
		self.errors = []
		if "errors" in json_clef:
			print (f"Found an error for clef {self.id}")
			for json_error in json_clef["errors"]:
				self.errors.append(Error (json_error))
		
	def overwrite (self, replacement):
		self.symbol.label = replacement["label"]
		self.height  = replacement["line"]
		if "octave_change" in replacement:
			self.octave_change =  replacement["octave_change"]
	def __str__(self):
		return f"Clef {self.symbol} {self.height}"
	def get_notation_clef(self):
		# Decode the DMOS infos
		return score_notation.Clef.decode_from_dmos(self.symbol.label, 
													self.height,
													self.id,
													self.octave_change)

class TimeSignature:
	"""
		Representation of a time signature
	"""
	
	def __init__(self, json_time_sign):
		if "id" in json_time_sign:
			self.id  = json_time_sign["id"]
		else:
			self.id = None

		self.element =   json_time_sign["element"]
		self.time =   json_time_sign["time"]
		self.unit =   json_time_sign["unit"]

		if "region" in json_time_sign:
			self.region = Region(json_time_sign["region"])
		else:
			self.region = None
		self.errors = []
		if "errors" in json_time_sign:
			for json_error in json_time_sign["errors"]:
				self.errors.append(Error (json_error))

	def overwrite (self, replacement):
		self.unit = replacement["unit"]
		self.time = replacement["time"]
		if "type" in replacement:
			self.element  = replacement["type"]

	def get_notation_object(self):
		# Decode the DMOS infos
		ts = score_notation.TimeSignature (self.time, self.unit, 
											id_ts=self.id)
		if self.element == "letter":
			ts.symbolize()
		elif self.element == "singleDigit":
			ts.set_single_digit()
		return ts
		
	def __str__ (self):
		return f"TimeSignature id: {self.id} ({self.time}  /  {self.unit}) (element: {self.element})"

	
	@staticmethod
	def build_from_notation_key(notation_tsign):
		# Used if we want to reinject in the DMOS file a missing time signature
		time_sign = {"id": notation_tsign.id,
		            "time": notation_tsign.numer,
		 			"unit": notation_tsign.denom,
		 			"element": "none"}
		return TimeSignature(time_sign)

class KeySignature:
	"""
		Representation of a key signature
	"""
	
	def __init__(self, json_key_sign):
		if "id" in json_key_sign:
			self.id  = json_key_sign["id"]
		else:
			self.id = None

		self.element =   json_key_sign["element"]
		self.nb_alterations =   json_key_sign["nb_alterations"]

		if "nb_naturals" in json_key_sign:
			self.nb_naturals =   json_key_sign["nb_naturals"]
		else:
			self.nb_naturals = 0
		if "region" in json_key_sign:
			self.region = Region(json_key_sign["region"])
		else:
			self.region = None
		self.errors = []
		if "errors" in json_key_sign:
			for json_error in json_key_sign["errors"]:
				self.errors.append(Error (json_error))
		
	def nb_sharps(self):
		if self.element == SHARP_SYMBOL:
			return self.nb_alterations
		else:
			return 0
	def nb_flats(self):
		if self.element == FLAT_SYMBOL:
			return self.nb_alterations
		else:
			return 0
	def get_notation_object(self):
		# Decode the DMOS infos
		return score_notation.KeySignature (self.nb_sharps(), 
										self.nb_flats(),
										id_key=self.id)

	def overwrite (self, replacement):
		nb_sharps = nb_flats = 0
		if "nb_sharps" in replacement.keys():
			nb_sharps = replacement["nb_sharps"]
		if "nb_flats" in replacement.keys():
			nb_flats = replacement["nb_flats"]
		
		if nb_sharps == 0 and nb_flats == 0:
			self.element = SHARP_SYMBOL
			self.nb_alterations = 0
		elif nb_sharps > 0:
			self.element = SHARP_SYMBOL
			self.nb_alterations = nb_sharps
		elif nb_flats > 0:
			self.element = FLAT_SYMBOL
			self.nb_alterations = nb_flats
	
	def __str__ (self):
		return f"KeySignature ({self.nb_sharps()} sharps, {self.nb_flats()} flats)"

	@staticmethod
	def build_from_notation_key(notation_key):
		# Used if we want to reinject in the DMOS file a missing key
		key_sign = {"element": notation_key.alter_type(),
		 			"nb_alterations": notation_key.nb_alters()}
		return KeySignature(key_sign)

class Error:
	"""
		Representation of an error met during OMR
	"""
	
	def __init__(self, json_error):
		self.message =   json_error["message"]
		if "confidence" in json_error:
			self.confidence = json_error["confidence"]
		else:
			self.confidence = None
	
	def __str__(self):
		return f"DMOS error '{self.message} with confidence {self.confidence}"

class Duration:
	"""
		Representation of a musical duration
	"""

	def __init__(self, json_duration):
		self.whole = False
		if "symbol" in json_duration:
			#
			# OLD FORMAT: TO REMOVE WHEN OBSOLETE
			self.symbol = Symbol (json_duration["symbol"])
			self.note_type = self.symbol.label
		else:
			self.note_type = json_duration["label"]

		self.nb_points = 0
		if "nb_points" in json_duration:
			self.nb_points = json_duration["nb_points"]
		self.decode_dmos_input()
		
	def decode_dmos_input(self):
		if self.note_type not  in DURATION_SYMBOLS_LIST:
			raise CScoreParserError (f'Unknown symbol name: {self.note_type}')

		# Sanity : we merge possible values for eighth notes
		if self.note_type == SMB_8TH_NOTE_SYN:
			self.note_type = SMB_8TH_NOTE
			
		if self.note_type == SMB_WHOLE_NOTE or self.note_type == SMB_WHOLE_REST:
			self.whole = True
			self.numer, self.denom =   4, 1
		elif self.note_type == SMB_HALF_NOTE or self.note_type == SMB_HALF_REST:
			self.numer, self.denom =   2, 1
		elif self.note_type == SMB_QUARTER_NOTE or self.note_type == SMB_QUARTER_REST:
			self.numer, self.denom =   1, 1
		elif self.note_type == SMB_8TH_NOTE or self.note_type == SMB_8TH_REST:
			self.numer, self.denom =   1, 2
		elif self.note_type == SMB_16TH_NOTE or self.note_type== SMB_16TH_REST:
			self.numer, self.denom =   1, 4
		elif self.note_type == SMB_32TH_NOTE or self.note_type == SMB_32TH_REST:
			self.numer, self.denom =   1, 8
		elif self.note_type == SMB_64TH_NOTE or self.note_type == SMB_64TH_REST:
			self.numer, self.denom =   1, 16
		elif self.note_type == SMB_128TH_NOTE or self.note_type == SMB_128TH_REST:
			self.numer, self.denom =   1, 32
		elif self.note_type == SMB_256TH_NOTE or self.note_type == SMB_256TH_REST:
			self.numer, self.denom =   1, 64

		if self.nb_points == 1:
			rational_fraction = Fraction (self.numer * 1.5 /  self.denom)
			self.numer, self.denom = rational_fraction.numerator, rational_fraction.denominator
			
		if self.nb_points == 2:
			rational_fraction = Fraction (self.numer * 1.75 / self.denom)
			self.numer, self.denom = rational_fraction.numerator, rational_fraction.denominator

	def overwrite (self, edition):
		#print (f"Received edition {edition}")
		if "duration" in edition:
			self.note_type = edition['duration']
		if "dots" in edition:
			self.nb_points = edition['dots']
		else:
			# By default, the number of dots is 0
			self.nb_points = 0
		self.decode_dmos_input()

class TupletInfo:
	"""
		Info for tuplets
	"""
	
	def __init__(self, json_tinfo):
		self.num = json_tinfo["num"]
		self.num_base = int (json_tinfo["numbase"])
	
class StaffHeader:
	"""
		Representation of a system header
	"""
	
	def __init__(self, json_system_header):
		self.id_part = StaffHeader.make_id_part (json_system_header["id_part"])
		self.no_staff = StaffHeader.make_id_staff( json_system_header['no_staff'])
		if "name" in json_system_header:
			self.part_name = json_system_header["name"]
		else:
			self.part_name = None
		if "first_bar" in json_system_header:
			self.first_bar = Segment(json_system_header["first_bar"])
		else:
			self.first_bar = None
		if "region" in json_system_header:
			self.region = Region(json_system_header["region"])
		else:
			self.region = None

	@staticmethod
	def make_id_staff (no_staff):
		return f"Staff{no_staff}"
	
	@staticmethod
	def make_id_part (id_part):
		return f"part{id_part}"
	
class MeasureHeader:
	"""
		Representation of a measure header
	"""
	
	def __init__(self, json_measure_header):
		self.no_staff = StaffHeader.make_id_staff(json_measure_header["no_staff"] )
		self.region = None 
		self.clef = None 
		self.key_signature = None 
		self.time_signature = None 
		self.type= "Unknown"
		self.id_elem = None 
		
		if "region" in json_measure_header:
			self.region = Region (json_measure_header["region"])
		if "clef" in json_measure_header:
			self.clef = Clef(json_measure_header["clef"])
			self.type = "Clef"
			self.id_elem = self.clef.id 
		if "key_signature" in json_measure_header:
			self.key_signature = KeySignature(json_measure_header["key_signature"])
			self.type = "Key signature"
			self.id_elem = self.key_signature.id 
		if "time_signature" in json_measure_header:
			self.time_signature  = TimeSignature(json_measure_header["time_signature"])
			self.type = "Time signature"
			self.id_elem = self.time_signature.id 

	def __str__(self):
		return f"Staff {self.no_staff} Clef {self.clef} KS: {self.key_signature} TS: {self.time_signature}"

class CScoreParserError(Exception):
	def __init__(self, *args):
		if args:
			self.message = args[0]
		else:
			self.message = None

	def __str__(self):
		if self.message:
			return 'CollabScore error, {0} '.format(self.message)
		else:
			return 'CollabScore error has been raised'

