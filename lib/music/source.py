
import json

import lib.music.Score as score_mod
import lib.music.notation as score_notation

'''
  Classes describing sources of abstract scores: images, audio, etc.
  
  Used mostly to map the structure of a score with components of the source
  via the concept of "Manifest" inspired by IIIF 
'''

class ScoreImgPart:
	'''
	   Core structure of a score = parts. We keep the id, name,
	    abbrevation
	 '''

	def __init__(self, id_part, name, abbreviation) :
		self.id = id_part
		self.name = name
		self.abbreviation = abbreviation

	def to_json (self):
		return {"id": self.id, "name": self.name,
			     "abbreviation": self.abbreviation}
	
	@staticmethod
	def from_json (json_part):
		return ScoreImgPart(json_part["id"], json_part["name"], json_part["abbreviation"])
	
class ScoreImgManifest:
	'''
		Describes the organization of an image of set of images 
		representing a score, as a list of pages, each page
		made of systems, and systems of staves. Staves
		are mapped to parts of the score
	'''
	
	def __init__(self, id_source, url) :
		self.id = id_source
		self.url = url
		# List of pages
		self.pages = []
		# List of parts. A dictionary because parts'id is unique
		self.parts = {}
		
	def add_page(self, page):
		self.pages.append(page)

	def get_page(self, nb):
		for page in self.pages:
			if page.number == nb:
				return page
		
		# Oups should never happpen
		raise score_mod.CScoreModelError ("Searching a non existing page : " + nb )
	
	def add_part(self, part):
		self.parts[part.id] = part
		
	def get_parts(self):
		return self.parts.values()
	
	@staticmethod
	def from_json (json_mnf):
		manifest = ScoreImgManifest( json_mnf["id"], json_mnf["url"])

		for json_page in json_mnf["pages"]:
			page = ScoreImgPage.from_json(json_page)
			manifest.add_page(page)

		for json_part in json_mnf["parts"]:
			part = ScoreImgPart.from_json(json_part)
			manifest.add_part(part)
			
		return manifest

	def to_json (self):
		pages_json = []
		for page in self.pages:
			pages_json.append(page.to_json())
		parts_json = []
		for part in self.get_parts():
			parts_json.append(part.to_json())
		return {"id": self.id, "url": self.url,
			     "pages": pages_json, "parts": parts_json}

	def print (self):
		print (json.dumps(self.to_json()))
		
class ScoreImgPage:
	'''
		A page of the score, containing systems
	'''
	
	def __init__(self, url, nb):
		self.url  = url
		self.number = nb
		self.systems  = []

	def add_system(self, system):
		self.systems.append(system)
		
	def get_system(self, nb):
		for system in self.systems:
			if system.number == nb:
				return system
		
		# Oups should never happpen
		raise score_mod.CScoreModelError (f"Searching a non existing system {nb} in page {self.number}")
	
	@staticmethod
	def from_json (json_mnf):
		page = ScoreImgPage(json_mnf["url"], json_mnf["number"])
		for json_system in json_mnf["systems"]:
			system = ScoreImgSystem.from_json(json_system)
			page.add_system(system)

		return page

	def to_json (self):
		systems_json = []
		for system in self.systems:
			systems_json.append(system.to_json())
		return {"url": self.url, "number": self.number, "systems": systems_json}

class ScoreImgSystem:
	'''
		A system in a page, containing staves
	'''
	
	def __init__(self, number) :
		self.number = number
		self.staves  = []

	def add_staff(self, staff):
		self.staves.append(staff)
		
	def get_staff(self, id_staff):
		for staff in self.staves:
			if staff.id == id_staff:
				return staff
		
		# Oups should never happpen
		raise score_mod.CScoreModelError (f"Searching a non existing staff {in_staff} in system {self.number}")

	@staticmethod
	def from_json (json_mnf):
		system = ScoreImgSystem(json_mnf["number"])
		for json_staff in json_mnf["staves"]:
			staff = ScoreImgStaff.from_json(json_staff)
			system.add_staff(staff)
		return system

	def to_json (self):
		staves_json = []
		for staff in self.staves:
			staves_json.append(staff.to_json())
		return {"number": self.number, "staves": staves_json}

		
class ScoreImgStaff:
	'''
		A staff in a system, which contains one or several parts
		(referred to by their id)
	'''
	
	def __init__(self, id_staff) :
		self.id = id_staff
		# Sometimes the time signature is implicit from the context
		# and we must add it
		self.time_signature = None
		self.parts  = []

	def add_part(self, id_part):
		self.parts.append(id_part)
		
	def to_json (self):
		obj =  {"id": self.id,
			     "parts": self.parts
			    }
		if self.time_signature is not None:
			obj["time_signature"] = self.time_signature.to_json()
		return obj
	
	@staticmethod
	def from_json (json_mnf):
		staff = ScoreImgStaff(json_mnf["id"])
		for id_part in json_mnf["parts"]:
			staff.add_part(id_part)
		if "time_signature" in json_mnf:
			print ("Found a time signature ")
			staff.time_signature = ScoreImgTimeSig.from_json(json_mnf["time_signature"])
		return staff
		
class ScoreImgTimeSig:
	"""
	  Sometimes we must add the time signature
	"""
	def __init__(self, count, unit) :
		self.count = count
		self.unit  = unit

	def to_json (self):
		return {"count": self.count,
			     "unit": self.unit
			    }
		
	def get_notation_object(self):
		return score_notation.TimeSignature (self.count, self.unit)
	
	
	@staticmethod
	def from_json (json_ts):
		return ScoreImgTimeSig(json_ts["count"], json_ts["unit"])

	