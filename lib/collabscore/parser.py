
import  sys, os
# import the logging library
import logging

import json
import jsonref
from pprint import pprint
from jsonref import JsonRef
import jsonschema 

# Get an instance of a logger
logger = logging.getLogger(__name__)

class CollabScoreParser:
	"""

		A class to parse a JSON document provided by the OMR tool 
		and to produce encoded scores

	"""

	def __init__(self, schema_file_path, base_uri=""):
		"""
		   Load the schema of OMR json files, for type checking
		   
		   See https://python-jsonschema.readthedocs.io/en/latest/
		"""
		
		sch_file = open(schema_file_path)
		self.schema  = json.load(sch_file)
	
		# The schema containes references to sub-files that need to be solved
		self.resolver = jsonschema.RefResolver(referrer=self.schema, 
										base_uri=base_uri)

		# Check schema via class method call. Works, despite IDE complaining
		self.validator = jsonschema.Draft4Validator (self.schema, resolver=self.resolver)
		
		# Might raise an exception
		jsonschema.Draft4Validator.check_schema(self.schema)
		
		return

	def validate_data (self, json_content):
		# Might raise an exception
		try:
			jsonschema.validate (instance=json_content, 
							schema=self.schema, 
							resolver=self.resolver)
		except jsonschema.ValidationError as ex:
			errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
			raise Exception ("Data  validation error: " + errors)
		except jsonschema.SchemaError as ex:
			raise Exception ("Data  validation error: " + str(ex))

"""
  Utility classes
"""

class OmrScore:
	"""
	  A structured representation of the score supplied by the OMR tool
	"""
	def __init__(self,json_data):
		"""
			Input: a validated JSON object. The method builds
			a representation based on the Python classes
		"""
		self.score_image_url = json_data["score_image_url"]
		self.date = json_data["date"]
		self.pages = []
		
		# Analyze pages
		for json_page in json_data["pages"]:
			self.pages.append(Page(json_page))

class Zone:
	"""
		A rectangular zone that frames a score graphical element
	"""
	
	def __init__(self,json_zone):
		self.xmin = json_zone[0]
		self.xmax = json_zone[1]
		self.ymin = json_zone[2]
		self.ymax = json_zone[3]

	def __str__(self):
		return f'({self.xmin},{self.ymin},{self.xmax},{self.ymax})'
	
	
class Symbol:
	"""
		An uninterpreted symbol (e.g, a Clef)
	"""
	def __init__(self, json_symbol):
		self.label = json_symbol["label"]
		self.zone = Zone(json_symbol["zone"])
		
class Element:
	"""
		An a score element 
	"""
	
	def __init__(self, json_elt):
		self.label = json_elt["label"]
		self.zone = Zone(json_elt["zone"])

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
		self.zone = Zone (json_system["zone"])
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
		self.zone = Zone (json_measure["zone"])
		self.voices =[]
		for json_voice in json_measure["voices"]:
			self.voices.append(Voice(json_voice))

class Voice:
	"""
		An voice containing voice elements
	"""
	
	def __init__(self, json_voice):
		self.items =[]
		
class VoiceItem:
	"""
		A voice item
	"""
	
	def __init__(self, json_voice):
		self.items =[]

##############

class Clef:
	"""
		Representation of a clef
	"""
	
	def __init__(self, json_clef):
		self.symbol =  Symbol (json_clef["symbol"])
		self.id_staff  = json_clef["id_staff"]
		self.height  = json_clef["height"]

class KeySignature:
	"""
		Representation of a key signature
	"""
	
	def __init__(self, json_key_sign):
		self.element =   json_key_sign["element"]
		self.nb_naturals =   json_key_sign["nb_naturals"]
		self.nb_alterations =   json_key_sign["nb_alterations"]

class TimeSignature:
	"""
		Representation of a time signature
	"""
	
	def __init__(self, json_time_sign):
		self.element =   json_time_sign["element"]
		self.time =   json_time_sign["time"]
		self.unit =   json_time_sign["unit"]

class StaffHeader:
	"""
		Representation of a system header
	"""
	
	def __init__(self, json_system_header):
		self.id_staff =json_system_header["id_staff"]
		self.first_bar = Element(json_system_header["first_bar"])

class MeasureHeader:
	"""
		Representation of a measure header
	"""
	
	def __init__(self, json_measure_header):
		self.clef = Clef(json_measure_header["clef"])
		self.key_signature = KeySignature(json_measure_header["key_signature"])
		self.time_signature  = TimeSignature(json_measure_header["time_signature"])

