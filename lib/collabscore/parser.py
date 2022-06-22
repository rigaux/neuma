
# import the logging library
import logging

import json
import jsonref
from jsonref import JsonRef
import jsonschema

from fractions import Fraction


import lib.music.Score as score_model
import lib.music.Voice as voice_model
import lib.music.events as score_events
import lib.music.notation as score_notation
import lib.music.annotation as annot_mod
import lib.music.constants as constants_mod

import verovio


from .constants import *

# Get an instance of a logger
# See https://realpython.com/python-logging/

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


# Create file handler
f_handler = logging.FileHandler(__name__ + '.log')
f_handler.setLevel(logging.DEBUG)
# Create formatters and add it to handlers
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
# Add handlers to the logger
logger.addHandler(f_handler)

# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
#logger.addHandler(c_handler)


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
				path = ""
				for p in e.absolute_path:
					path += str(p) + '/' 
				str_errors += " Error : " + e.message + " (path " + path + ")"
			raise Exception ("Schema  validation error: " + str_errors)
		except jsonschema.SchemaError as ex:
			errors = sorted(self.validator.iter_errors(self.schema), key=lambda e: e.path)
			str_errors = ""
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
			errors = sorted(self.validator.iter_errors(json_content), key=lambda e: e.path)
			str_errors = ""
			for e in errors:
				path = ""
				for p in e.absolute_path:
					path += str(p) + '/' 
				str_errors += " Error : " + e.message + " (path " + path + ")"
			raise Exception ("Data  validation error: " + str_errors)
		except jsonschema.SchemaError as ex:
			errors = sorted(self.validator.iter_errors(json_content), key=lambda e: e.path)
			str_errors = ""
			for e in errors:
				path = ""
				for p in e.absolute_path:
					path += str(p) + '/' 
					print ("Path to error " + path)
				str_errors += " Error : " + e.message + " (path " + path + ")"
			raise Exception (ex.message)

"""
  Utility classes
"""

class OmrScore:
	"""
	  A structured representation of the score supplied by the OMR tool
	"""
	def __init__(self, uri, json_data):
		"""
			Input: a validated JSON object. The method builds
			a representation based on the Python classes
		"""
		self.uri = uri 
		self.id = json_data["id"]
		self.score_image_url = json_data["score_image_url"]
		self.date = json_data["date"]
		
		self.creator = annot_mod.Creator ("collabscore", 
										annot_mod.Creator.SOFTWARE_TYPE, 
										"collabscore")
		self.pages = []
		# Analyze pages
		for json_page in json_data["pages"]:
			self.pages.append(Page(json_page))


	def get_score(self):
		'''
			Builds a score (instance of our score model) from the Omerized document
		'''
		
		score = score_model.Score()
		current_measure_no = 0
		
		for page in self.pages:
			for system in page.systems:
				# Headers defines the parts and their staves in this system
				for header in system.headers:
					if score.part_exists(header.id_part):
						part = score.get_part(header.id_part)
					else:
						part = score_model.Part(id_part=header.id_part)
						score.add_part(part)
					# Add the staff
					part.add_staff (score_notation.Staff(header.no_staff))
					
				# Now we scan the measures. DMOS gives us a measure
				# for all the parts of the system. Therefore we add 
				# one measure to each part, and add the voice to the measure
				# based on its part_id assignment
				
				for measure in system.measures:
					current_measure_no += 1
					logger.info (f'Process measure {current_measure_no}')
					
					# Create a new measure for each part
					current_measures = {}
					for part in score.parts:
						# IMPORTANT: Works for a part with a single staff. Else, we probably need to
						# add a measure for each staff. 
						
						measure_for_part = score_model.Measure(current_measure_no)
						
						# Annotate this measure
						'''annotation = annot_mod.Annotation.create_annot_from_xml_to_image(
							self.creator, self.uri, measure_for_part.id, 
							self.score_image_url, measure.region.string_xyhw(), 
							constants_mod.IREGION_MEASURE_CONCEPT)
						score.add_annotation (annotation)'''
						
						# Check if the measure starts with a change of clef or meter
						for header in measure.headers:
							if part.staff_exists(header.no_staff):
								staff = part.get_staff (header.no_staff)
								if header.clef is not None:
									clef_staff = header.clef.get_notation_clef()
									staff.set_current_clef (clef_staff)
									measure_for_part.add_clef (clef_staff)
								if header.time_signature is not None:
									logger.info (f'Time signature found on staff {header.no_staff} at measure {current_measure_no}')
									time_sign = header.time_signature.get_notation_object()
									# staff.add_time_signature (current_measure_no, time_sign)
									measure_for_part.add_time_signature (time_sign)
						# Add the measure to its part (notational events are added there)
						part.append_measure (measure_for_part)
						# Keep the array of current measures indexed by part
						current_measures[part.id] = measure_for_part

					for voice in measure.voices:
						# Get the part the voice belongs to
						current_part = score.get_part(voice.id_part)
						current_measure = current_measures[voice.id_part]
						
						# Reset the event counter
						score_events.Event.reset_counter(
							f'{voice.id_part}m{current_measure.id}{voice.id}')

						# Create the voice
						voice_part = voice_model.Voice(id=voice.id)
						for item in voice.items:
							(event, event_region) = self.decode_event(current_part, item) 
							voice_part.append_event(event)
							# Annotate this event
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
						# Add the voice to the measure of the relevant part
						current_measure.add_voice (voice_part)
		
		return score 


	def decode_event(self, part, voice_item):
		'''
			Produce an event (from our score model) and its region by decoding the OMR input
		'''
		
		# Duration of the event: the DMOS encoding is 1 from whole note, 2 for half, etc.
		# Our encoding (music21) is 1 for quarter note. Hence the computation
		duration = score_events.Duration(voice_item.duration.numer, voice_item.duration.denom)
		
		# The symbol in the duration contains the region of the event
		if 	voice_item.duration.symbol.region is None:
			logger.error ("A voice item without region has been met")
			raise CScoreParserError ("A voice item without region has been met")
		event_region = voice_item.duration.symbol.region

		if voice_item.note_attr is not None:
			# It should be a note
			for head in voice_item.note_attr.heads:
				staff = part.get_staff (head.no_staff)
				# The head position gives the position of the note on the staff
				(pitch_class, octave)  = staff.current_clef.decode_pitch (head.height)
			
				# Decode from the DMOS input codification
				if head.alter == None:
					alter = score_events.Note.ALTER_NONE
				elif head.alter.label == FLAT_SYMBOL:
					alter = score_events.Note.ALTER_FLAT
				elif head.alter.label  == SHARP_SYMBOL:
					alter = score_events.Note.ALTER_SHARP
					
				# Did we just met an accidental?
				if (alter != score_events.Note.ALTER_NONE):
					logger.info (f'Accidental {alter} met on staff {staff.id}')
					staff.add_accidental (pitch_class, alter)
				else:
					# Is there a previous accidental on this staff for this pitch class?
					alter = staff.get_accidental(pitch_class)
					
				# Only manage one head 
				break
			event = score_events.Note(pitch_class, octave, duration, alter, head.no_staff)
		elif voice_item.rest_attr is not None:
			# It is a rest
			for head in voice_item.rest_attr.heads:
				staff = part.get_staff (head.no_staff)
			event = score_events.Rest(duration, head.no_staff)
		else:
			logger.error ("A voice event with unknown type has been met")
			raise CScoreParserError ("A voice event with unknown type has been met")
		return (event, event_region)

class Point:
	"""
		A geometric point
	"""
	
	def __init__(self,json_point):
		self.x = json_point[0]
		self.y = json_point[1]

	def __str__(self):
		return f'(Point({self.x},{self.y})'

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
		

	def __str__(self):
		return f'({self.label},{self.region})'

class Page:
	"""
		An page containing systems
	"""
	
	def __init__(self, json_page):
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
		self.id_part = json_voice["id_part"]
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
		
		self.duration = Duration (json_voice_item["duration"])
		if "no_group" in json_voice_item:
			self.no_group = json_voice_item["no_group"]
		if "direction" in json_voice_item:
			self.direction = json_voice_item["direction"]
		if "att_note" in json_voice_item:
			self.note_attr = NoteAttr (json_voice_item["att_note"])
		if "att_rest" in json_voice_item:
			# NB: using the same type for note heads and rest heads
			self.rest_attr = NoteAttr (json_voice_item["att_rest"])
		if "att_clef" in json_voice_item:
			self.clef_attr  = Clef (json_voice_item["att_clef"])
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
		for json_head in json_note_attr["heads"]:
			self.heads.append(Note (json_head))

##############

class Note:
	"""
		Representation of a Note
	"""
	
	def __init__(self, json_note):
		self.tied = False
		self.alter = None

		self.head_symbol =  Symbol (json_note["head_symbol"])
		self.no_staff  = json_note["no_staff"]
		self.height  = json_note["height"]
		
		if "alter" in json_note:
			self.alter = Symbol (json_note["alter"])
		if "tied" in json_note:
			self.tied = json_note["tied"]


class Clef:
	"""
		Representation of a clef
	"""
	
	def __init__(self, json_clef):
		self.symbol =  Symbol (json_clef["symbol"])
		self.height  = json_clef["height"]

	def get_notation_clef(self):
		# Decode the DMOS infos
		return score_notation.Clef.decode_from_dmos(self.symbol.label, self.height)
		
class KeySignature:
	"""
		Representation of a key signature
	"""
	
	def __init__(self, json_key_sign):
		self.element =   json_key_sign["element"]
		self.nb_naturals =   json_key_sign["nb_naturals"]
		self.nb_alterations =   json_key_sign["nb_alterations"]
		

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
		if self.symbol.label not  in DURATION_SYMBOLS_LIST:
			raise CScoreParserError (f'Unknown symbol name: {self.symbol.label}')
		if self.symbol.label == SMB_WHOLE_NOTE or self.symbol.label == SMB_WHOLE_REST:
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
		return score_notation.TimeSignature (self.time, self.unit)

class StaffHeader:
	"""
		Representation of a system header
	"""
	
	def __init__(self, json_system_header):
		self.id_part =json_system_header["id_part"]
		self.no_staff =json_system_header["no_staff"]
		if "first_bar" in json_system_header:
			self.first_bar = Segment(json_system_header["first_bar"])

class MeasureHeader:
	"""
		Representation of a measure header
	"""
	
	def __init__(self, json_measure_header):
		self.no_staff = json_measure_header["no_staff"] 
		self.clef = None 
		self.key_signature = None 
		self.time_signature = None 
		
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
			return 'CollabScoreParserError, {0} '.format(self.message)
		else:
			return 'CollabScoreParserError has been raised'

