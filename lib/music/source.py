
import json

'''
  Classes describing sources of abstract scores: images, audio, etc.
  
  Used mostly to map the structure of a score with components of the source
  via the concept of "Manifest" inspired by IIIF 
'''

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
		self.pages = []
		
	def add_page(self, page):
		self.pages.append(page)
		
	@staticmethod
	def from_json (json_mnf):
		manifest = ScoreImgManifest( json_mnf["id"], json_mnf["url"])

		for json_page in json_mnf["pages"]:
			page = ScoreImgPage.from_json(json_page)
			manifest.add_page(page)
			
		return manifest

	def to_json (self):
		pages_json = []
		for page in self.pages:
			pages_json.append(page.to_json())
		return {"id": self.id, "url": self.url,
			     "pages": pages_json}

	def print (self):
		print (json.dumps(self.to_json()))
		
class ScoreImgPage:
	'''
		A page of the score, containing systems
	'''
	
	def __init__(self, url, number) :
		self.url  = url
		self.number = number
		self.systems  = []

	def add_system(self, system):
		self.systems.append(system)
		
	@staticmethod
	def from_json (json_mnf):
		page = ScoreImgPage(json_mnf["url"], json_mnf["number"])
		return page

	def to_json (self):
		systems_json = []
		for system in self.systems:
			systems_json.append(system.to_json())
		return {"url": self.url, "number": self.number, "staves": systems_json}

class ScoreImgSystem:
	'''
		A system in a page, containing staves
	'''
	
	def __init__(self, number) :
		self.number = number
		self.staves  = []

	def add_staff(self, staff):
		self.staves.append(staff)

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
		self.parts  = []

	def add_part(self, id_part):
		self.parts.append(id_part)
		
	def to_json (self):
		return {"id": self.id,
			     "parts": self.parts
			    }
		
		
