import json

import lib.music.Score as score_mod
import lib.music.notation as notation_mod
import lib.music.iiifutils as iiif_mod
from lib.music.Score import Part
from collections import OrderedDict

'''
 A class used to represent a source (multimedia document) associated to an Opus
'''

class OpusSource:
	'''
		A source (digital document referring to an Opus)
	'''
	
	# Codes for normalized references
	DMOS_REF = "dmos"
	MEI_REF = "ref_mei"
	IIIF_REF = "iiif"
	MIDI_REF = "midi"
	MUSICXML_REF = "musicxml"
	TMP_REF = "tmp"
		
	def __init__(self, ref, source_type, mime_type, url):
		self.ref = ref
		self.source_type = source_type
		self.mime_type = mime_type
		self.url  = url
		self.file_path = None
		self.has_manifest = False
		self.description = ""
		self.images = []

	def get_iiif_manifest(self):
		# IIIF extraction: only for sources of type IIIF_REF
		if self.ref == self.IIIF_REF:
			iiif_proxy = iiif_mod.Proxy(iiif_mod.GALLICA_BASEURL)
			self.images = []
			# Extract the document identifier			
			docid = iiif_mod.Proxy.decompose_gallica_ref(self.url)
			try:
				document = iiif_proxy.get_document(docid)
				for i in range(document.nb_canvases):
					canvas = document.get_canvas(i)
					self.images.append(canvas.get_image(0))
			except Exception as ex:
				score_mod.logger.info(str(ex))
		
	def to_json (self):
		source_dict =  {
			"ref": self.ref, 
			"description": self.description,
			"source_type": self.source_type, 
			"mime_type": self.mime_type, 
			"url": self.url,
			"file_path": self.file_path,
			"has_manifest": self.has_manifest}
		
		if self.ref == self.IIIF_REF and len(self.images) > 0:
			source_dict["images"] = []
			for img in self.images:
				source_dict["images"].append(img.to_dict())
		return source_dict

'''
  Classes describing sources of abstract scores: images, audio, etc.
  
  Used mostly to map the structure of a score with components of the source
  via the concept of "Manifest" inspired by IIIF 
'''


class Manifest:
	'''
		Describes the organization of an image of set of images 
		representing a score, as a list of pages, each page
		made of systems, and systems of staves. Staves
		are mapped to parts of the score
	'''
	
	def __init__(self, id_source, url, first_p_music=1) :
		self.id = id_source
		self.url = url
		# List of pages
		self.pages = []
		# List of parts. A dictionary because parts'id is unique
		self.parts = {}
		# Groups = parts with more than on staff
		self.groups = {}
		# Music can be found after x pages
		self.first_music_page = first_p_music
		self.nb_empty_pages = self.first_music_page - 1
		
	def add_page(self, page):
		self.pages.append(page)

	def get_page(self, nb):
		for page in self.pages:
			if page.number == nb:
				return page
		
		# Oups should never happpen
		raise score_mod.CScoreModelError (f"Searching a non existing page : {nb}" )

	def add_image_info(self, images):
		# Enrich the manifest with info coming from IIIF
		for page in self.pages:
			# print (f"Searching for page {page.url}")
			for img in images:
				if page.url == img.url:
					page.width = img.width
					page.height = img.height
					
	def get_first_music_page(self):	
		"""
		   Determine the first page of the source
		   where some music content has been parsed
		"""
		for page in self.pages:
			print (f"Page URL {page.url}")
			page_ref = iiif_mod.Proxy.find_page_ref(page.url)
			self.first_music_page = int(page_ref[1:])
			break
		self.nb_empty_pages = self.first_music_page - 1

	def clean_pages_url(self):	
		"""
		  Normalize the IIIF URLs
		"""
		for page in self.pages:
			page.url = iiif_mod.Proxy.find_page_id(page.url)

	def add_part(self, part):
		self.parts[part.id] = part

	def part_exists(self, id_part):
		return (id_part in self.parts.keys())

	def get_part(self, id_part):
		if not (id_part in self.parts.keys()):
			raise score_mod.CScoreModelError ("Searching a non existing part : " + id_part )		
		return self.parts[id_part]
			
	def get_parts(self):
		# Beware: depending on the order with which parts are discovered,
		# Part1 might appear before Part2 or the opposite: we sort
		
		# Create a dictionary
		dict_parts = {}
		for part in self.parts.values():
			dict_parts[part.id] = part 
		# Sort the dict
		sorted_dict = OrderedDict(sorted(dict_parts.items()))
		# Create the sorted array
		sorted_parts = []
		for part in sorted_dict.values():
			sorted_parts.append(part)
		# Finally we reverse: DMOS gives the parts bottom-up
		sorted_parts.reverse()
		return sorted_parts


	@staticmethod
	def from_json (json_mnf):
		manifest = Manifest( json_mnf["id"], json_mnf["url"], 
							json_mnf["first_music_page"])

		# First decode the parts
		for json_part in json_mnf["parts"]:
			part = MnfPart.from_json(json_part)
			manifest.add_part(part)
		
		# The gen the structure in pages / systems / staves
		for json_page in json_mnf["pages"]:
			page = MnfPage.from_json(json_page, manifest)
			manifest.add_page(page)

		# Analyze the structure to identify groups of staves (same part) 
		manifest.create_groups()
		
		return manifest

	def to_json (self):
		pages_json = []
		for page in self.pages:
			pages_json.append(page.to_json())
		parts_json = []
		for part in self.get_parts():
			parts_json.append(part.to_json())
		return {"id": self.id, "url": self.url, 
			     "first_music_page":self.first_music_page,
			     "pages": pages_json, "parts": parts_json}

	def create_groups(self):
		# Collect groups found in pages.
		# Warning: in an extreme case we must manage group at the system level
		for page in self.pages:
			page.create_groups()
			for id_part, staves in page.groups.items():
				if not id_part in self.groups.keys():
					score_mod.logger.info(f"Found a group for part {id_part}")
					self.groups[id_part] = staves

	def is_a_part_group (self, id_part):
		if id_part in self.groups.keys():
			return True
		else:
			return False
	
	def print (self):
		print (json.dumps(self.to_json()))

class MnfPart:
	'''
	   Core structure of a score = parts. We keep the id, name,
	    abbrevation
	 '''

	def __init__(self, id_part, name, abbreviation, instrument="piano") :
		self.id = id_part
		self.name = name
		self.abbreviation = abbreviation
		self.instrument = instrument

	def to_json (self):
		return {"id": self.id, "name": self.name,
			     "abbreviation": self.abbreviation}
	
	@staticmethod
	def from_json (json_part):
		return MnfPart(json_part["id"], json_part["name"], json_part["abbreviation"])
			
class MnfPage:
	'''
		A page of the score, containing systems
	'''
	
	def __init__(self, url, nb, width, height, manifest):
		self.manifest = manifest
		self.url  = url
		self.width = width
		self.height = height
		self.number = nb
		self.systems  = []
		self.groups = {}

	def add_system(self, system):
		self.systems.append(system)
		
	def get_system(self, nb):
		for system in self.systems:
			if system.number == nb:
				return system
		
		# Oups should never happpen
		raise score_mod.CScoreModelError (f"Searching a non existing system {nb} in page {self.number}")
	
	@staticmethod
	def from_json (json_mnf, manifest):
		page = MnfPage(json_mnf["url"], json_mnf["number"], 
					     json_mnf["width"], json_mnf["height"], manifest)
		for json_system in json_mnf["systems"]:
			system = MnfSystem.from_json(json_system, page)
			page.add_system(system)
		page.create_groups()

		return page

	def to_json (self):
		systems_json = []
		for system in self.systems:
			systems_json.append(system.to_json())
		return {"url": self.url, "number": self.number, 
			   "width": self.width, "height": self.height, 
			   "systems": systems_json}

	def create_groups(self):
		# Collect groups found in systems.
		# Warning: in an extreme case we must manage group at the system level
		for system in self.systems:
			system.create_groups()
			for id_part, staves in system.groups.items():
				if not id_part in self.groups.keys():
					score_mod.logger.info (f"Found a staff group in page {self.url} for part {id_part}")
					self.groups[id_part] = staves

class MnfSystem:
	'''
		A system in a page, containing staves
	'''
	
	def __init__(self, number, page, region=None) :
		self.page = page
		self.number = number
		self.staves  = []
		self.measures  = []
		self.groups = {}
		self.region = MnfRegion(region)

	def add_staff(self, staff):
		self.staves.append(staff)
		
	def get_staff(self, id_staff):
		for staff in self.staves:
			if staff.id == id_staff:
				return staff
		
		# Oups should never happpen
		raise score_mod.CScoreModelError (f"Searching a non existing staff {id_staff} in system {self.number}")

	def add_measure(self, measure):
		self.measures.append(measure)
		
	def get_measure(self, no_measure):
		for measure in self.measures:
			if measure.number_in_system == no_measure:
				return measure
		# Oups should never happpen
		raise score_mod.CScoreModelError (f"Searching the manifest for a non existing measure {no_measure} in system {self.number}")

	@staticmethod
	def from_json (json_mnf, page):
		system = MnfSystem(json_mnf["number"], page, json_mnf["region"])
		for json_staff in json_mnf["staves"]:
			staff = MnfStaff.from_json(json_staff, system)
			system.add_staff(staff)
		for json_measure in json_mnf["measures"]:
			measure = MnfMeasure.from_json(json_measure, system)
			system.add_measure(measure)
			
		system.create_groups()
		
		return system

	def to_json (self):
		staves_json = []
		for staff in self.staves:
			staves_json.append(staff.to_json())
		measures_json = []
		for measure in self.measures:
			measures_json.append(measure.to_json())
		return {"number": self.number, 
				"region": self.region.to_json(),
				"staves": staves_json,
				"measures": measures_json
				}

	def create_groups(self):
		# identify parts that spread over several staves (ie keyboards)
		parts_staves = {}
		for staff in self.staves:
			for part in staff.parts:
				if part.id in parts_staves.keys():
					parts_staves[part.id].append(staff)
				else:
					parts_staves[part.id] = [staff]
					
		# OK, now find parts with more that one staff
		for id_part, staves in parts_staves.items():
			if len(staves) > 1:
				score_mod.logger.info (f"Found a staff group in system {self.number} for part {id_part}")
				self.groups[id_part] = staves
	
	def count_staves_for_part (self, id_part):
		count = 0
		for staff in self.staves:
			for part in staff.parts:
				if part.id == id_part:
					count += 1
		return count
		
class MnfStaff:
	'''
		A staff in a system, which contains one or several parts
		(referred to by their id)
	'''
	
	def __init__(self, id_staff, system) :
		self.system = system
		self.id = id_staff
		# Sometimes the time signature is implicit from the context
		# and we must add it
		self.time_signature = None
		
		# In principle we might have a list of parts on a same staff
		self.parts  = []
		
		# The local staff number tells us the id of the staff
		# in a part with multiple staves
		self.number_in_part = 1
		
		# The "local" part is a combination of the part ID and the staff number
		# for this part. In case of a part "P1" with two staves, we will have for
		# instance "P1-1" for the first staff and "P1-2" for the second. Useful
		# for music21 StaffGroups structures
		self.local_part_id = ""
		
	def contains_part(self, id_part):
		for part in self.parts:
			if part.id == id_part:
				return True
			else:
				return False
	
	def get_part_id(self):
		# For the time being we allow only one part per staff
		
		if len(self.parts) > 1 or len(self.parts) == 0:
			raise score_mod.CScoreModelError (f"Staff {self.id} should have exactly one part")
		return self.parts[0].id
		
	def add_part(self, id_part):
		# For the time being we allow only one part per staff
		
		if len(self.parts) > 0:
			raise score_mod.CScoreModelError (f"Cannot add several parts to a same staff. Not yet implemented")

		self.parts.append(self.system.page.manifest.get_part(id_part))
		
		# How many staves for this part in the current system?
		self.number_in_part = self.system.count_staves_for_part (id_part) 
		
		# Warning: will not work in case we have several parts
		self.local_part_id = score_mod.Part.make_part_id(id_part, self.number_in_part)

	def clear_and_replace_part(self, id_part):
		# Clear the parts, add a new one
		self.parts = []
		self.add_part (id_part)

	def replace_part(self, source, target):
		# Replace part 'source' with part 'target'
		for part in self.parts:
			if part.id == source.id:
				# Still assuming one part per staff
				self.parts = [target] 
				# Update the number of staves and the local part id
				self.number_in_part = self.system.count_staves_for_part (target.id) 
				self.local_part_id = score_mod.Part.make_part_id(target.id, self.number_in_part)
		
	def to_json (self):
		partids = []
		for part in self.parts:
			partids.append(part.id)
			
		obj =  {"id": self.id,
			     "parts": partids
			    }
		if self.time_signature is not None:
			obj["time_signature"] = self.time_signature.to_json()
		return obj
	
	@staticmethod
	def from_json (json_mnf, system):
		staff = MnfStaff(json_mnf["id"], system)
		for id_part in json_mnf["parts"]:
			staff.add_part(id_part)
		if "time_signature" in json_mnf:
			staff.time_signature = MnfTimeSig.from_json(json_mnf["time_signature"])
		return staff

		
class MnfMeasure:
	'''
		A measure in a system, covering all the staves
	'''
	
	def __init__(self, no_measure, no_in_system, mei_id, system, region) :
		self.system = system
		self.number = no_measure
		self.number_in_system = no_in_system
		self.mei_id = mei_id
		self.region = MnfRegion(region)				
		
	def to_json (self):
		return {"number": self.number, 
				"number_in_system": self.number_in_system, 
				"mei_id": self.mei_id,
				"region": self.region.to_json()}
	
	@staticmethod
	def from_json (json_measure, system):
		measure = MnfMeasure(json_measure["number"], 
							json_measure["number_in_system"], 
							json_measure["mei_id"], 
							system, json_measure["region"])
		return measure
	
class MnfTimeSig:
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
		return notation_mod.TimeSignature (self.count, self.unit)
	
	
	@staticmethod
	def from_json (json_ts):
		return MnfTimeSig(json_ts["count"], json_ts["unit"])

class MnfPoint:
	"""
		A geometric point
	"""
	
	def __init__(self, point):
		self.x = point[0]
		self.y = point[1]

	@staticmethod
	def from_json (json_point):
		return MnfPoint(json_point)

	def to_json(self):
		return [self.x, self.y]
	
	#def __str__(self):
	#	return f'(Point({self.x},{self.y})'
	def __str__(self):
		return [self.x,self.y]

class MnfRegion:
	"""
		A polygon described by its contour
	"""
	
	def __init__(self, region=None):
		self.contour = []
		if region is not None:
			for point in region:
				self.contour.append(MnfPoint(point))

	def __str__(self):
		str_repr =""
		for point in self.contour:
			str_repr += str(point)

		return f'({str_repr})'
	
	def to_json(self):
		res = []
		for pt in self.contour:
			res.append (pt.to_json())
		return res
	
	@staticmethod
	def from_json (json_region):
		region = []
		for json_point in json_region:
			region.append(MnfPoint(json_point))
		return MnfRegion(region)


