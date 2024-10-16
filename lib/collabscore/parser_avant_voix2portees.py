
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
from lib.music.source import Manifest
from numpy.testing.utils import measure


# Get an instance of a logger
# See https://realpython.com/python-logging/

#logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# Create file handler
f_handler = logging.FileHandler(__name__ + '.log')
f_handler.setLevel(logging.INFO)
# Create formatters and add it to handlers
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
# Add handlers to the logger
logger.addHandler(f_handler)

# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.INFO)
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
#logger.addHandler(c_handler)

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
		print (f"Parser configuration:\nLog level={self.log_level}\n" +
		         f"page_min={self.page_min}\npage_max={self.page_max}\n" +
		         f"system_min={self.system_min}\nsystem_max={self.system_max}\n" +
			     f"measure_min={self.measure_min}\nmeasure_max={self.measure_max}")
			
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
		self.uri = uri 
		self.id = 1 #json_data["id"]
		self.score_image_url = "http://" # json_data["score_image_url"]
		#self.date = json_data["date"]
		self.json_data = json_data
		
		self.creator = annot_mod.Creator ("collabscore", 
										annot_mod.Creator.SOFTWARE_TYPE, 
										"collabscore")
		# Edit operations applied to the score 
		self.editions = []
		for op in editions:
			self.editions.append (op)

		# Decode the DMOS input as Python objects
		self.pages = []
		for json_page in self.json_data["pages"]:
			page = Page(json_page)							
			self.pages.append(page)

		# Produce the manifest of the score
		current_page_no = 0
		self.manifest = Manifest(json_data["id"], json_data["score_image_url"])
		for page in self.pages:
			current_system_no = 0
			current_page_no += 1
			# Create the manifest from the source
			src_page = source_mod.MnfPage(page.page_url, current_page_no, 0, 0,
										self.manifest)
			for system in page.systems:
				current_system_no += 1
				src_system = source_mod.MnfSystem(current_system_no, src_page,
												system.region.to_json())
				src_page.add_system(src_system)
				
				for header in system.headers:
					src_staff = source_mod.MnfStaff(header.no_staff, src_system)
					src_system.add_staff(src_staff)
					if self.manifest.part_exists (header.id_part):
						# Ok this part is spread over several staves
						src_part = self.manifest.get_part (header.id_part)
					else:
						# It is a new part 
						src_part = source_mod.MnfPart(header.id_part, header.id_part, header.id_part) 
						self.manifest.add_part(src_part)
					src_staff.add_part(header.id_part)
			self.manifest.add_page(src_page)
		
		# Now we create the groups to detect parts that extend over several staves
		self.manifest.create_groups()
		
		# Clean pages URL and find the first page of music
		self.manifest.clean_pages_url()
		self.manifest.get_first_music_page()
		
		# Apply editions related to the manifest
		for edition in self.editions:
			edition.apply_to(self)
		
		self.config = ParserConfig(config)
		self.config.print()		
		
	def get_score(self):
		'''
			Builds a score (instance of our score model) from the Omerized document
		'''		
		# Create an OMR score (with layout)
		score = score_model.Score(use_layout=False)
		
		# 
		# The manifest tells us the parts of the score: we create them
		for src_part in self.manifest.get_parts():
			# Parts are identified by the part id + staff id. In general
			# there is only on staff per part
			print ("Processing part " + src_part.id)
			if not self.manifest.is_a_part_group(src_part.id):
				id_part_staff = score_model.Part.make_part_id(src_part.id, "1")
				part = score_model.Part(id_part=id_part_staff, name=src_part.name, 
												abbreviation=src_part.abbreviation)
				score.add_part(part)			
				logger.info (f"Add a single-staff part {id_part_staff}")
				print (f"Add a single-staff part {id_part_staff}")
			else:
				# It is a part group. Create one PartStaff for each staff of the part 
				staff_group = []
				i_staff = 1
				for staff in self.manifest.groups[src_part.id]:
					id_part_staff = score_model.Part.make_part_id(src_part.id, i_staff)
					i_staff+= 1
					part = score_model.Part(id_part=id_part_staff, name=src_part.name, 
												abbreviation=src_part.abbreviation,
												part_type="partstaff")
					logger.info (f"Add a staff part {id_part_staff} in a part group")
					staff_group.append(part.m21_part)
					score.add_part(part)
				# + a Staff grouo for the global part
				part_group = score_model.Part(id_part=src_part.id, name=src_part.name, 
												abbreviation=src_part.abbreviation,
												part_type="group", group=staff_group)
				logger.info (f"Add a part group {src_part.id} with {i_staff-1} staff-parts")
				score.add_part(part_group)
	
		logger.info (f"")
		logger.info (f"== End of score structure creation. Scanning pages ===")

		# Main scan: we fill the parts with measures
		current_page_no = 0
		current_measure_no = 0
		current_position = 0
		
		for json_page in self.json_data["pages"]:
			current_page_no += 1
			current_system_no = 0
			if (current_page_no < self.config.page_min) or (
					    current_page_no > self.config.page_max):
				continue
			page = Page(json_page)							

			logger.info (f"")
			logger.info (f'Process page {current_page_no}')

			# Get the page from the manifest
			mnf_page = self.manifest.get_page(current_page_no)
			
			#print (f"Processing page {current_page_no}")
			page_begins = True
			
			for system in page.systems:
				current_system_no += 1
				current_system_measure_no = 0
				if (current_page_no == self.config.page_min 
				      and current_system_no < self.config.system_min) or (
					    current_page_no == self.config.page_max and 
					       current_system_no > self.config.system_max):
					continue

				logger.info (f"")
				logger.info (f'Process system {current_system_no}')

				# Get the system from the manifest
				mnf_system = mnf_page.get_system(current_system_no)

				# Annotate this measure
				annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, f"P{current_page_no}-S{current_system_no}", 
							page.page_url, system.region.string_xyhw(), 
							constants_mod.IREGION_SYSTEM_CONCEPT)
				score.add_annotation (annotation)

				#score_system = score_model.System(system.id)
				#score_page.add_system(score_system)
				system_begins = True
				
				# We clear the staves for all parts of the score: maybe a part
				# is not represented in this specific system
				previous_staves = {}
				for part in score.parts:
					# keep the previous staff: it contains info about current clef, etc 
					previous_staves[part.id] = part.staves
					part.clear_staves()
					
				# Headers defines the parts and their staves in this system
				for header in system.headers:
					# Get the staff from the manifest
					mnf_staff = mnf_system.get_staff(header.no_staff)
					score_part_id = mnf_staff.local_part_id
					if score.part_exists(score_part_id):
						#logger.info (f"Add staff {header.no_staff} to part {score_part_id}")
						part = score.get_part(score_part_id)
						# Add the staff to the system
						staff = score_notation.Staff(header.no_staff)
						# See what we inherit from the previous staves of the part
						if score_part_id in previous_staves.keys():
							for prev_staff in previous_staves[score_part_id]:
								#logger.info(f"Inherited TS for part {score_part_id} (in staff {prev_staff.id}):  {prev_staff.current_time_signature}")
								staff.set_current_time_signature(prev_staff.current_time_signature)
								
							# See if the manifest gives an explicit time signature
							if mnf_staff.time_signature is not None:
								staff.set_current_time_signature (mnf_staff.time_signature.get_notation_object())
							part.add_staff (staff)			
					else:
						# Should not happen: parts have been created once for all
						logger.error (f"Part {score_part_id} should have been already created")
					
				# Now, for the current system, we know the parts and the staves for 
				# each part, initialized with their time signatures
				# We scan the measures. DMOS gives us a measure for all the parts of the system. 
				# We add one measure to each part.
				
				initial_measure = True
				for measure in system.measures:
					current_position = score.duration().quarterLength
					#print (f'Process measure {current_measure_no}, to be inserted at position {current_position}')
					current_measure_no += 1
					current_system_measure_no += 1
					if (current_page_no == self.config.page_min 
				      	and current_system_no == self.config.system_min
				      	and current_system_measure_no < self.config.measure_min) or (
					    current_page_no == self.config.page_max 
					    and current_system_no == self.config.system_max
					    and current_system_measure_no > self.config.measure_max):
						continue
				
					# Accidentals are reset at the beginning of measures
					score.reset_accidentals()
					
					logger.info (f"")
					logger.info (f'Process measure {current_measure_no}, to be inserted at position {score.duration()}')

					# Annotate this measure
					annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, f"P{current_page_no}-S{current_system_no}-M{current_measure_no}", 
							page.page_url, measure.region.string_xyhw(), 
							constants_mod.IREGION_MEASURE_CONCEPT)
					score.add_annotation (annotation)

					# Create a new measure for each part
					current_measures = {}
					for part in score.get_parts():
						# We ignore the part if it does not have a staff for the current system
						'''if not part.has_staves():
							print (f"Skipping measure {current_measure_no} for part {part.id}")
							continue
						'''
						measure_for_part = score_model.Measure(part, current_measure_no)
						# Adding score, pages and system breaks
						if 	page_begins and current_page_no > 1:
							measure_for_part.add_page_break()
							page_begins = False
							system_begins = False
						elif system_begins and current_system_no > 1:
							## Add a system break
							measure_for_part.add_system_break()
							system_begins = False

								
						# Add the measure to its part (notational events are added there)
						part.append_measure (measure_for_part)
						# Keep the array of current measures indexed by part
						current_measures[part.id] = measure_for_part
						
					# Measure headers (DMOS) tells us, for each staff, if 
					# one starts with a change of clef or meter
					new_time_signature = None
					for header in measure.headers:
						# Identify the part, staff and measure, from the staff id
						id_part = mnf_system.get_staff(header.no_staff).local_part_id
						part = score.get_part (id_part)
						staff = part.get_staff (header.no_staff)
						measure_for_part = current_measures[part.id]
						
						if header.region is not None:
							# Record the region of the measure for the current staff
							annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
									self.creator, self.uri, measure_for_part.id, 
									page.page_url, header.region.string_xyhw(), 
									constants_mod.IREGION_MEASURE_STAFF_CONCEPT)
							score.add_annotation (annotation)
						if header.clef is not None:
							clef_staff = header.clef.get_notation_clef()
							staff.set_current_clef (clef_staff)
							logger.info (f'Clef {clef_staff} found on staff {header.no_staff} at measure {current_measure_no}')
							measure_for_part.set_initial_clef_for_staff(staff.id, clef_staff)
						if header.time_signature is not None:
							new_time_signature = header.time_signature.get_notation_object()
							logger.info (f'Time signature  {new_time_signature} found on staff {header.no_staff} at measure {current_measure_no}')
							staff.set_current_time_signature (new_time_signature)
							measure_for_part.add_time_signature (new_time_signature)
						else:
							if initial_measure:
								# Rare occurrence: no time signature on the
								# initial measure: we hope it is stored in the staff
								logger.warning (f'No time signature at the beginning of staff {header.no_staff}. We take {staff.current_time_signature}')
								ts = staff.current_time_signature.copy()
								measure_for_part.add_time_signature (ts)
								staff.set_current_time_signature (ts)
		
							# Sanity: we found at least one time signature change, it should
							# apply to all staves
							if new_time_signature is not None:
								logger.warning (f'Using the time signature already found on another staff:  {new_time_signature}')
								ts = new_time_signature.copy()
								staff.set_current_time_signature (ts)
								measure_for_part.add_time_signature (ts)
								
						if header.key_signature is not None:
							key_sign = header.key_signature.get_notation_object()
							logger.info (f'Key signature {key_sign} found on staff {header.no_staff} at measure {current_measure_no}')
							# The key signature impacts all subsequent events on the staff
							staff.set_current_key_signature (key_sign)
							# We will display the key signature at the beginning
							# of the current measure
							measure_for_part.add_key_signature (key_sign)
					
					# Now we scan the voices
					for voice in measure.voices:
						# DMOS gives has 'id_part' the staff where
						# the first voice event appears. From this staff, we deduce
						# the part the voice belongs to
						mnf_staff = mnf_system.get_staff(voice.id_staff)
						current_part = score.get_part(mnf_staff.local_part_id)
						current_staff = current_part.get_staff (voice.id_staff)
						current_measure = current_measures[current_part.id]

						logger.info (f"")
						logger.info (f'Process voice {voice.id}, on staff {voice.id_staff} in part {current_part.id}')
						
						# Reset the event counter
						score_events.Event.reset_counter(
							f'F{current_page_no}{voice.id_part}M{current_measure.id}{voice.id}')

						# Create the voice
						voice_part = voice_model.Voice(part=current_part,voice_id=voice.id)
						# The initial clefs are those of the measure
						voice_part.set_current_clefs(current_measure.initial_clefs)
						# The current time signature is useful to decode whole notes
						voice_part.set_current_time_signature(current_staff.current_time_signature)
						# We disable automatic beaming
						voice_part.automatic_beaming = False
						
						current_beam = None						
						previous_event = None
						for item in voice.items:
							# Duration exception: in case of "whole" note, depends 
							# on the time signature
							if item.duration.whole:
								item.duration.numer =  voice_part.current_time_signature.numer
								item.duration.denom = 1
								
							# Decode the event
							(event, event_region, type_event) = self.decode_event(voice_part, item) 
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
								voice_part.append_event(event)
							elif type_event == "clef":
								# The staff id is in the voice item
								no_staff = item.no_staff_clef
								# We found a clef change
								voice_part.append_clef(event, no_staff)
							else:
								logger.error (f'Unknown event type {type_event} for voice {voice.id}')
		
							# Annotate this event if the region is known
							# We do not do that for the moment
							if event_region is not None:
								annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
									self.creator, self.uri, event.id, 
									self.score_image_url, event_region.string_xyhw(), 
									constants_mod.IREGION_NOTE_CONCEPT)
								score.add_annotation (annotation)
							
							# Did we met errors ?
							for error in item.errors:
								annotation = annot_mod.Annotation.create_annot_from_error (
									self.creator, self.uri, event.id, error.message, 
									constants_mod.OMR_ERROR_UNKNOWN_SYMBOL)
								score.add_annotation (annotation)
								
						# End of items for this measure. Close any pending beam
						if current_beam != None:
							#print (f"Stop beam {current_beam}")
							previous_event.stop_beam(current_beam)
							current_beam =  None
							
						# Clean the voice of possible inconsistencies. For
						# instance ties that to not make sense
						voice_part.clean()
						
						# Add the voice to the measure of the relevant part
						current_measure.add_voice (voice_part)
						
						
						# This is not longer the initial measure of the system
						initial_measure = False		
					
					# Checking consistency of time signatures
					score.check_time_signatures(current_measures)
					
					
					# Time to check the consistency of the measure
					for measure in	current_measures.values():
						measure.check_consistency()
						
		return score


	def decode_event(self, voice, voice_item):
		'''
			Produce an event (from our score model) and its region by decoding the OMR input
		'''
		
		# Duration of the event: the DMOS encoding is 1 from whole note, 2 for half, etc.
		# Our encoding (music21) is 1 for quarter note. Hence the computation
		duration = score_events.Duration(voice_item.duration.numer * voice_item.tuplet_info.num_base, 
										voice_item.duration.denom * voice_item.tuplet_info.num)
		
		# The symbol in the duration contains the region of the event
		#  We accept events without region, to simplify the JSON notation
		event_region = voice_item.duration.symbol.region

		if voice_item.note_attr is not None:
			# It can be a note or a chord
			events = []
			for head in voice_item.note_attr.heads:
				no_staff = StaffHeader.make_id_staff(head.no_staff) # Will be used as the chord staff.
				current_clef = voice.get_current_clef_for_staff(no_staff)
				# The head position gives the position of the note on the staff
				(pitch_class, octave)  = current_clef.decode_pitch (head.height)
			
				# Get the default alter
				staff = voice.part.get_staff(no_staff)
				# Did we just met an accidental?
				if (head.alter != score_events.Note.ALTER_NONE):
					logger.info (f'Accidental {head.alter} met on staff {staff.id}')
					staff.add_accidental (pitch_class, head.alter)
					alter = head.alter
				else:
					# The staff records the status of accidentals
					alter = staff.get_accidental(pitch_class)

				logger.info (f'Adding note {pitch_class}{octave}-{alter} to staff {no_staff} with current clef {staff.current_clef}.')
					
				note = score_events.Note(pitch_class, octave, duration, alter, head.no_staff)
				# Check ties
				if head.tied and head.tied=="forward":
					#print (f"Tied note start with id {head.id_tie}")
					note.start_tie()
				if head.tied and head.tied=="backward":
					#print (f"Tied note ends with id {head.id_tie}")
					note.stop_tie()
				
				# Check articulations
				for json_art in head.articulations:
					if json_art["label"] in ARTICULATIONS_LIST:
						articulation = score_events.Articulation(json_art["placement"], json_art["label"])
						note.add_articulation(articulation)
					elif json_art["label"] in EXPRESSIONS_LIST:
						expression = score_events.Expression(json_art["placement"], json_art["label"])
						note.add_expression(expression)
					elif json_art["label"] in DYNAMICS_LIST:
						dynamic = score_notation.Dynamics(json_art["placement"], json_art["label"])
						# A dynamic is inserted in the music flow
						#events.append(dynamic)
				events.append(note)
				
			if len(events) == 1:
				# A single note
				event = events[0]
			else:
				# A chord
				event = score_events.Chord (duration, no_staff, events)
				# REPEATED: factorize with above
				for json_art in head.articulations:
					if json_art["label"] in ARTICULATIONS_LIST:
						articulation = score_events.Articulation(json_art["placement"], json_art["label"])
						event.add_articulation(articulation)
					elif json_art["label"] in EXPRESSIONS_LIST:
						expression = score_events.Expression(json_art["placement"], json_art["label"])
						event.add_expression(expression)
					elif json_art["label"] in DYNAMICS_LIST:
						dynamic = score_notation.Dynamics(json_art["placement"], json_art["label"])
						# A dynamic is inserted in the music flow
						#events.append(dynamic)

		elif voice_item.rest_attr is not None:
			# It is a rest
			for head in voice_item.rest_attr.heads:
				event = score_events.Rest(duration, head.no_staff)
			event.set_visibility(voice_item.rest_attr.visible)
		elif voice_item.clef_attr is not None:
			#This is a clef change 
			event = voice_item.clef_attr.get_notation_clef()
			event_region = voice_item.clef_attr.symbol.region
			return (event, event_region, "clef")
		else:
			logger.error ("A voice event with unknown type has been met")
			raise CScoreParserError ("A voice event with unknown type has been met")
		
		return (event, event_region, "event")

	def write_as_musicxml(self, out_file):
		self.get_score().write_as_musicxml (out_file)

	def write_as_mei(self, out_file):
		self.get_score().write_as_mei (out_file)

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
		for json_system in json_page["systems"]:
			self.systems.append(System(json_system))

class System:
	"""
		An sytem containing measures
	"""
	
	def __init__(self, json_system):
		self.id = json_system["id"]
		self.region = Region (json_system["region"])
		self.headers = []
		for json_header in json_system["headers"]:
			self.headers.append(StaffHeader(json_header))
		self.measures = []
		for json_measure in json_system["measures"]:
			self.measures.append(Measure(json_measure))

class Measure:
	"""
		An measure containing voices
	"""
	
	def __init__(self, json_measure):
		if "region" in json_measure:
			self.region = Region (json_measure["region"])
		self.headers =[]
		for json_header in json_measure["headers"]:
			self.headers.append(MeasureHeader(json_header))
		self.voices =[]
		for json_voice in json_measure["voices"]:
			self.voices.append(Voice(json_voice))

class Voice:
	"""
		An voice containing voice elements
	"""
	
	def __init__(self, json_voice):
		self.id = json_voice["id"]
		self.id_part =  StaffHeader.make_id_part ( json_voice["id_part"])
		# Obsolete, since a voice can spread several parts
		self.id_staff =  StaffHeader.make_id_staff ( json_voice["id_part"])
		
		self.items = []
		for json_item in json_voice["elements"]:
			self.items.append(VoiceItem (json_item))
			
		
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
		
		self.duration = Duration (json_voice_item["duration"])
		if "no_group" in json_voice_item:
			no_group = json_voice_item["no_group"]
			# Assume that 0 is a no-value
			if no_group > 0:
				self.beam_id = json_voice_item["no_group"]
				
		if "tuplet_info" in json_voice_item:
			self.tuplet_info = TupletInfo (json_voice_item["tuplet_info"])

		if "direction" in json_voice_item:
			self.direction = json_voice_item["direction"]
		if "att_note" in json_voice_item:
			self.note_attr = NoteAttr (json_voice_item["att_note"])
		if "att_rest" in json_voice_item:
			# NB: using the same type for note heads and rest heads
			self.rest_attr = NoteAttr (json_voice_item["att_rest"])
		if "att_clef" in json_voice_item:
			self.clef_attr  = Clef (json_voice_item["att_clef"])
			self.no_staff_clef = StaffHeader.make_id_staff(json_voice_item["att_clef"]["no_staff"])
		self.errors = []
		if "errors" in json_voice_item:
			for json_error in json_voice_item["errors"]:
				self.errors.append(Error (json_error))

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
		if "visible" in json_note_attr:
			self.visible = json_note_attr["visible"]
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
		self.tied  = "none"
		self.id_tie = 0
		self.alter = score_events.Note.ALTER_NONE

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

class Clef:
	"""
		Representation of a clef
	"""
	
	def __init__(self, json_clef):
		self.symbol =  Symbol (json_clef["symbol"])
		self.height  = json_clef["height"]
		
	def get_notation_clef(self):
		# Decode the DMOS infos
		return score_notation.Clef.decode_from_dmos(self.symbol.label, 
												self.height)
		
class KeySignature:
	"""
		Representation of a key signature
	"""
	
	def __init__(self, json_key_sign):
		self.element =   json_key_sign["element"]
		self.nb_naturals =   json_key_sign["nb_naturals"]
		self.nb_alterations =   json_key_sign["nb_alterations"]
		
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
		return score_notation.KeySignature (self.nb_sharps(), self.nb_flats())

class Error:
	"""
		Representation of an error met during OMR
	"""
	
	def __init__(self, json_error):
		self.message =   json_error["message"]

class Duration:
	"""
		Representation of a musical duration
	"""

	def __init__(self, json_duration):
		self.symbol = Symbol (json_duration["symbol"])
		self.whole = False
		
		if self.symbol.label not  in DURATION_SYMBOLS_LIST:
			raise CScoreParserError (f'Unknown symbol name: {self.symbol.label}')
		if self.symbol.label == SMB_WHOLE_NOTE or self.symbol.label == SMB_WHOLE_REST:
			self.whole = True
			self.numer, self.denom =   4, 1
		elif self.symbol.label == SMB_HALF_NOTE or self.symbol.label == SMB_HALF_REST:
			self.numer, self.denom =   2, 1
		elif self.symbol.label == SMB_QUARTER_NOTE or self.symbol.label == SMB_QUARTER_REST:
			self.numer, self.denom =   1, 1
		elif self.symbol.label == SMB_8TH_NOTE or self.symbol.label == SMB_8TH_REST:
			self.numer, self.denom =   1, 2
		elif self.symbol.label == SMB_16TH_NOTE or self.symbol.label == SMB_16TH_REST:
			self.numer, self.denom =   1, 4
		elif self.symbol.label == SMB_32TH_NOTE or self.symbol.label == SMB_32TH_REST:
			self.numer, self.denom =   1, 8

		self.nb_points = 0
		if "nb_points" in json_duration:
			self.nb_points = json_duration["nb_points"]
		if self.nb_points == 1:
			rational_fraction = Fraction (self.numer * 1.5 /  self.denom)
			self.numer, self.denom = rational_fraction.numerator, rational_fraction.denominator
		if self.nb_points == 2:
			rational_fraction = Fraction (self.numer * 1.75 / self.denom)
			self.numer, self.denom = rational_fraction.numerator, rational_fraction.denominator



class TupletInfo:
	"""
		Info for tuplets
	"""
	
	def __init__(self, json_tinfo):
		self.num = json_tinfo["num"]
		self.num_base = int (json_tinfo["numbase"])

class TimeSignature:
	"""
		Representation of a time signature
	"""
	
	def __init__(self, json_time_sign):
		self.element =   json_time_sign["element"]
		self.time =   json_time_sign["time"]
		self.unit =   json_time_sign["unit"]

	def get_notation_object(self):
		# Decode the DMOS infos
		ts = score_notation.TimeSignature (self.time, self.unit)
		if self.element == "letter":
			ts.symbolize()
		return ts
	
class StaffHeader:
	"""
		Representation of a system header
	"""
	
	def __init__(self, json_system_header):
		self.id_part = StaffHeader.make_id_part (json_system_header["id_part"])
		self.no_staff = StaffHeader.make_id_staff( json_system_header['no_staff'])
		if "first_bar" in json_system_header:
			self.first_bar = Segment(json_system_header["first_bar"])

	@staticmethod
	def make_id_staff (no_staff):
		return f"Staff{no_staff}"
	
	@staticmethod
	def make_id_part (id_part):
		return f"Part{id_part}"
	
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
		
		if "region" in json_measure_header:
			self.region = Region (json_measure_header["region"])
		if "clef" in json_measure_header:
			self.clef = Clef(json_measure_header["clef"])
		if "key_signature" in json_measure_header:
			self.key_signature = KeySignature(json_measure_header["key_signature"])
		if "time_signature" in json_measure_header:
			self.time_signature  = TimeSignature(json_measure_header["time_signature"])

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

