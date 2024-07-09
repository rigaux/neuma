
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
		self.config = ParserConfig(config)
		self.config.print()		

		self.uri = uri 
		self.id = 1 #json_data["id"]
		self.score_image_url = "http://" # json_data["score_image_url"]
		#self.date = json_data["date"]
		self.json_data = json_data
		
		# The Score, obtained after a call to get_score
		self.score = None 
		
		self.creator = annot_mod.Creator ("collabscore", 
										annot_mod.Creator.SOFTWARE_TYPE, 
										"collabscore")
		# Edit operations applied to the score 
		self.editions = []
		for op in editions:
			self.editions.append (op)

		# Editions to apply to the outpu MusicXML
		self.post_editions = []
		
		# Decode the DMOS input as Python objects
		self.pages = []
		for json_page in self.json_data["pages"]:
			page = Page(json_page)							
			self.pages.append(page)

		# Produce the manifest of the score
		current_page_no = 0
		current_measure_no = 0
		# We need to initialize the interpretation context
		self.initial_key_signature = None
		self.initial_time_signature = None
		initial_measure = True 

		self.manifest = Manifest(json_data["id"], json_data["score_image_url"])
		for page in self.pages:
			current_system_no = 0
			current_page_no += 1
			# Create the manifest from the source
			src_page = source_mod.MnfPage(page.page_url, current_page_no, 0, 0,
										self.manifest)
			for system in page.systems:
				current_system_no += 1
				current_system_measure_no = 0
				src_system = source_mod.MnfSystem(current_system_no, src_page,
												system.region.to_json())
				src_page.add_system(src_system)
				
				count_staff_per_part = {}
				for header in system.headers:
					src_staff = source_mod.MnfStaff(header.no_staff, src_system)
					src_system.add_staff(src_staff)
					if self.manifest.part_exists (header.id_part):
						# This part has already been met
						src_part = self.manifest.get_part (header.id_part)
					else:
						# It is a new part 
						src_part = source_mod.MnfPart(header.id_part, header.id_part, header.id_part) 
						self.manifest.add_part(src_part)
						
					# Count the number of staves for the part
					if header.id_part in count_staff_per_part.keys():
						count_staff_per_part[header.id_part] += 1
					else:
						count_staff_per_part[header.id_part] = 1
						
					src_staff.add_part(header.id_part)
					
				for measure in system.measures:
					current_measure_no += 1
					current_system_measure_no += 1
					src_measure = source_mod.MnfMeasure(current_measure_no, 
													  current_system_measure_no,
													  "", # So far we do not know the MEI id
													  src_system,
														measure.region.to_json())
					src_system.add_measure(src_measure)
					
					# Search for an initial time and key signature in the
					# initial measure header
					if initial_measure:
						for header in measure.headers:
							# Identify the part, staff and measure, from the staff id
							if header.time_signature is not None and self.initial_time_signature is None:
								self.initial_time_signature = header.time_signature.get_notation_object()
							if header.key_signature is not None and self.initial_key_signature is None:
								self.initial_key_signature = header.key_signature.get_notation_object()

						if self.initial_key_signature is None:
							# Whaouh, no key signature on the initial measure
							self.initial_key_signature = score_notation.KeySignature()
							logger.error (f"Missing key signature at the beginning of the score. Taking {self.initial_key_signature}")						
						if self.initial_time_signature is None:
							# Whaouh, no time signature on the initial measure
							self.initial_time_signature = score_notation.TimeSignature()
							logger.error (f"Missing time signature at the beginning of the score. Taking {self.initial_time_signature}")						
					initial_measure = False

			self.manifest.add_page(src_page)
		
		# Now we create the groups to detect parts that extend over several staves
		self.manifest.create_groups()
		
		# Clean pages URL and find the first page of music
		self.manifest.clean_pages_url()
		self.manifest.get_first_music_page()
		
		# Apply editions related to the manifest
		for edition in self.editions:
			edition.apply_to(self)
		

	def get_score(self):
		'''
			Builds a score (instance of our score model) from the Omerized document
		'''		
		# Create an OMR score (with layout)
		if self.score != None:
			print ("The score has already been computed. We return the version in cache")
			return self.score # Returning the score in cache
		
		# The score has not yet been computed
		score = score_model.Score(use_layout=False)
		
		# Set initial context
		logger.info (f"Initial time signature set to {self.initial_time_signature}")						
		score.current_key_signature = self.initial_key_signature
		logger.info (f'Initial key signature set to {self.initial_key_signature}')
		score.current_time_signature = self.initial_time_signature

		# 
		# The manifest tells us the parts of the score: we create them
		for src_part in self.manifest.get_parts():
			# Parts are identified by the part id + staff id. In general
			# there is only on staff per part
			if not self.manifest.is_a_part_group(src_part.id):
				id_part_staff = score_model.Part.make_part_id(src_part.id)
				part = score_model.Part(id_part=id_part_staff, name=src_part.name, 
												abbreviation=src_part.abbreviation)
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
				# + a Staff grouo for the global part
				part_group = score_model.Part(id_part=src_part.id, name=src_part.name, 
												abbreviation=src_part.abbreviation,
												part_type=score_model.Part.GROUP_PART, 
												group=staff_group)
				logger.info (f"Add a part group {src_part.id} with {i_staff} staff-parts")
				score.add_part(part_group)
	
		logger.info (f"")
		logger.info (f"== End of score structure creation. Scanning pages ===")

		# Main scan: we fill the parts with measures
		current_page_no = 0
		current_measure_no = 0
		
		for json_page in self.json_data["pages"]:
			current_page_no += 1
			current_system_no = 0
			if not self.config.in_range (current_page_no):
				continue
			
			page = Page(json_page)							

			logger.info (f"")
			logger.info (f'** Process page {current_page_no}')

			# Get the page from the manifest
			mnf_page = self.manifest.get_page(current_page_no)
			
			#print (f"Processing page {current_page_no}")
			page_begins = True
			
			for system in page.systems:
				system_begins = True
				current_system_no += 1
				current_system_measure_no = 0
				if not self.config.in_range (current_page_no, current_system_no):
					continue

				logger.info (f"")
				logger.info (f'*** Process system {current_system_no}')

				# Get the system from the manifest
				mnf_system = mnf_page.get_system(current_system_no)

				# Annotate this measure
				annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, f"P{current_page_no}-S{current_system_no}", 
							page.page_url, system.region.string_xyhw(), 
							constants_mod.IREGION_SYSTEM_CONCEPT)
				score.add_annotation (annotation)

				
				# Now, for the current system, we know the parts and the staves for 
				# each part, initialized with their time signatures
				# We scan the measures. DMOS gives us a measure for all the parts of the system. 
				# We add one measure to each part.
				
				for measure in system.measures:
					current_measure_no += 1
					current_system_measure_no += 1
					if not self.config.in_range (current_page_no, current_system_no, current_system_measure_no):
						logger.info (f'Skipping measure {current_measure_no}')
						continue
				
					logger.info (f"")
					logger.info (f'***** Process measure {current_measure_no}, to be inserted at position {score.duration().quarterLength}')

					# Get the measure from the manifest
					mnf_measure = mnf_system.get_measure(current_system_measure_no)

					# Accidentals are reset at the beginning of measures
					score.reset_accidentals()
					
					# Annotate this measure
					annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, f"P{current_page_no}-S{current_system_no}-M{current_measure_no}", 
							page.page_url, measure.region.string_xyhw(), 
							constants_mod.IREGION_MEASURE_CONCEPT)
					score.add_annotation (annotation)

					# Create a new measure for each part
					for part in score.get_parts():
						logger.info (f"Adding measure {current_measure_no} to part {part.id}")
						part.add_measure (current_measure_no)

						# Adding page and system breaks
						if 	page_begins and current_page_no > 1:
							part.add_page_break()
							page_begins = False
							system_begins = False
						elif system_begins and current_system_no > 1:
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
						
						if header.region is not None:
							# Record the region of the measure for the current staff
							annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
									self.creator, self.uri, measure_for_part.id, 
									page.page_url, header.region.string_xyhw(), 
									constants_mod.IREGION_MEASURE_STAFF_CONCEPT)
							score.add_annotation (annotation)
						if header.clef is not None:
							clef_staff = header.clef.get_notation_clef()
							clef_position = part.get_duration()
							logger.info (f'Clef {clef_staff} found on staff {header.no_staff} at measure {current_measure_no}, position {clef_position}')
							part.set_current_clef (clef_staff, mnf_staff.number_in_part, clef_position)
						if header.time_signature is not None:
							new_time_signature = header.time_signature.get_notation_object()
							logger.info (f'Time signature  {new_time_signature} found on staff {header.no_staff} at measure {current_measure_no}')
							# Setting the TS at the score level propagates to all parts
							score.set_current_time_signature (new_time_signature)
			
						if header.key_signature is not None:
							key_sign = header.key_signature.get_notation_object()
							logger.info (f'Key signature {key_sign} found on staff {header.no_staff} at measure {current_measure_no}')
							# The key signature impacts all subsequent events on the staff
							part.set_current_key_signature (key_sign)
							# We will display the key signature at the beginning
							# of the current measure
							measure_for_part.replace_key_signature (key_sign)
			
					# Now we scan the voices
					for voice in measure.voices:
						current_part = score.get_part(voice.id_part)

						logger.info (f"")
						logger.info (f'Process voice {voice.id} in part {current_part.id}')
						
						# Reset the event counter
						score_events.Event.reset_counter(
							f'F{current_page_no}{voice.id_part}M{current_measure_no}{voice.id}')

						# Create the voice
						voice_part = voice_model.Voice(part=current_part,voice_id=voice.id)
						voice_part.absolute_position = measure_for_part.absolute_position
						# We disable automatic beaming
						voice_part.automatic_beaming = False

						# Now we add events to the voice						
						current_beam = None						
						previous_event = None
						for item in voice.items:
							# Duration exception: in case of "whole" note, depends 
							# on the time signature
							if item.duration.whole:
								# A la blanche (4) ou autre (3/1, 3/2, 6/8, etc)
								item.duration.numer =  4* current_part.get_current_time_signature().numer 
								item.duration.denom = current_part.get_current_time_signature().denom
							# Decode the event
							(event, event_region, type_event) = self.decode_event(mnf_system, voice_part, item) 
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
							elif type_event == "clef":
								# The staff id is in the voice item
								id_staff = item.no_staff_clef
								mnf_staff = mnf_system.get_staff(id_staff)
								clef_position = measure_for_part.absolute_position + voice_part.get_duration()
								# We found a clef change
								logger.info (f"Add a clef to staff {id_staff} at position {clef_position}")
								current_part.set_current_clef (event, mnf_staff.number_in_part, clef_position)
							else:
								logger.error (f'Unknown event type {type_event} for voice {voice.id}')
		
							# Annotate this event if the region is known
							if event_region is not None:
								if event.is_chord():
									# We do not know how to assign an id to a chord, so we annotate the notes
									for note in event.notes:
										# Same region for all notes....
										annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
											self.creator, self.uri, note.id, 
											self.score_image_url, event_region.string_xyhw(), 
											constants_mod.IREGION_NOTE_CONCEPT)
										score.add_annotation (annotation)
								else:
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
													
						# Add the voice to the measure of the relevant part
						if voice_part.nb_events() > 0:
							# This functions computes the main staff of the voice
							current_part.add_measure_voice (voice_part)
							
							# Searching for events outside the main staff
							if current_part.part_type == score_model.Part.GROUP_PART:
								for event in voice_part.events:
									if event.is_note():
										move = self.move_to_correct_staff(event, voice_part.main_staff)
										if move is not None:
											self.post_editions.append(move)
									elif event.is_chord():
										for note in event.notes:
											move = self.move_to_correct_staff(note, voice_part.main_staff)
											if move is not None:
												self.post_editions.append(move)
						else:
							logger.warning (f"Found an empty voice {voice_part.id}. Ignored")
											
					# Checking consistency of time signatures
					logger.info("")
					logger.info("Checking time signatures")
					logger.info("")
					score.check_time_signatures()
		
					# Time to check the consistency of the measure
					logger.info("")
					logger.info("Checking consistency of measures")
					logger.info("")
					score.check_measure_consistency()
					
		# Aggrgate voices at the part level
		logger.info("")
		logger.info("Create part voices from measure voices")
		logger.info("")
		score.aggregate_voices_from_measures()
		# Now clean the voice of possible inconsistencies. For
		# instance ties that to not make sense
		score.clean_voices() 
	
		# Remove in the XML file the pseudo-beam
		self.post_editions.append( editions_mod.Edition (editions_mod.Edition.CLEAN_BEAM))

		self.score = score 			
		return self.score

	def move_to_correct_staff(self, note, main_staff):
		# Register an edition to move a note to its correct staff
		if note.no_staff != main_staff:
			if note.no_staff < main_staff:
				direction = "up"
			else:
				direction = "down"
			logger.info  (f"Moving note {note.get_code()} direction {direction} ")
			move = editions_mod.Edition (editions_mod.Edition.MOVE_OBJECT_TO_STAFF,
										{"object_id": note.id, 
										"staff_no": note.no_staff,
										"direction": direction})
			return move
		else:
			return None

	def decode_event(self, mnf_system, voice, voice_item):
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
				id_staff = StaffHeader.make_id_staff(head.no_staff) # Will be used as the chord staff.
				mnf_staff = mnf_system.get_staff(id_staff)
				
				# Get the sub-part where the event is positioned. Seen as a staff
				staff = voice.part.get_part_staff(mnf_staff.number_in_part)
				event_position = voice.absolute_position + voice.get_duration()
				current_clef = staff.get_clef_at_pos(event_position)

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
											mnf_staff.number_in_part, stem_direction=voice_item.direction)
				# Check ties
				if head.tied and head.tied=="forward":
					print (f"Tied note {note} start with id {head.id_tie}")
					note.start_tie(head.id_tie)
				if head.tied and head.tied=="backward":
					print (f"Tied note {note} ends with id {head.id_tie}")
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
			else:
				# A chord
				logger.info (f'Adding a chord with {len(events)} notes.')
				for event in events:
					logger.info (f'\tNote {event.pitch_class}{event.octave}-{event.alter}, duration {event.duration.get_value()} to staff {id_staff} with current clef {current_clef}.')
				event = score_events.Chord (duration, mnf_staff.number_in_part, events)
				self.add_expression_to_event(events, event, head.articulations)
		elif voice_item.rest_attr is not None:
			# It is a rest
			for head in voice_item.rest_attr.heads:
				id_staff = StaffHeader.make_id_staff(head.no_staff) # Will be used as the chord staff.
				mnf_staff = mnf_system.get_staff(id_staff)
				#staff = voice.part.get_staff(mnf_staff.number_in_part)

				id_staff = StaffHeader.make_id_staff(head.no_staff) # Will be used as the chord staff.
				event = score_events.Rest(duration, mnf_staff.number_in_part)
				event.set_visibility(voice_item.rest_attr.visible)
				logger.info (f'Adding rest {duration.get_value()} to staff {id_staff}.')
		elif voice_item.clef_attr is not None:
			#This is a clef change 
			event = voice_item.clef_attr.get_notation_clef()
			event_region = voice_item.clef_attr.symbol.region
			return (event, event_region, "clef")
		else:
			logger.error ("A voice event with unknown type has been met")
			raise CScoreParserError ("A voice event with unknown type has been met")
		
		return (event, event_region, "event")

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
		print ("Writing as MusicXML")
		self.get_score().write_as_musicxml (out_file)
		
		print ("\n\nApplying post-editions to the MusicXML file\n")
		for ed in self.post_editions:
			ed.apply_to(self, out_file)
			
	def write_as_mei(self, mxml_file, out_file):
		self.get_score().write_as_mei (mxml_file, out_file)

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
		#self.id_staff =  StaffHeader.make_id_staff ( json_voice["id_part"])
		
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

		self.direction = None
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
		if "id" in json_clef:
			self.id  = json_clef["id"]
		else:
			self.id = None

		self.symbol =  Symbol (json_clef["symbol"])
		self.height  = json_clef["height"]
		
	def get_notation_clef(self):
		# Decode the DMOS infos
		return score_notation.Clef.decode_from_dmos(self.symbol.label, 
													self.height,
													self.id)
		
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
		print (f"Decode KEY id = {self.id}")
		return score_notation.KeySignature (self.nb_sharps(), 
										self.nb_flats(),
										id_key=self.id)

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
		if "id" in json_time_sign:
			self.id  = json_time_sign["id"]
		else:
			self.id = None

		self.element =   json_time_sign["element"]
		self.time =   json_time_sign["time"]
		self.unit =   json_time_sign["unit"]

	def get_notation_object(self):
		# Decode the DMOS infos
		ts = score_notation.TimeSignature (self.time, self.unit, self.id)
		if self.element == "letter":
			ts.symbolize()
		elif self.element == "singleDigit":
			ts.set_single_digit()
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

