import json
import csv

import lib.music.Score as score_mod
import lib.music.notation as notation_mod

import lib.iiif.IIIF2 as iiif2_mod

from lib.music.Score import Part
from collections import OrderedDict
from pip._vendor.distlib import manifest

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
	AUDIO_REF = "audio"
	IIIF_REF = "iiif"
	SYNC_REF = "sync"
	MIDI_REF = "midi"
	MUSICXML_REF = "musicxml"
	TMP_REF = "tmp"
		
	def __init__(self, ref, source_type, mime_type, 
				url, metadata={}):
		self.ref = ref
		self.source_type = source_type
		self.mime_type = mime_type
		self.url  = url
		self.metadata = metadata
		self.file_path = None
		self.has_manifest = False
		self.has_iiif_manifest = False
		self.description = ""
		self.images = []

	def get_iiif_manifest(self):
		# IIIF extraction: only for sources of type IIIF_REF
		if self.ref == self.IIIF_REF:
			iiif_proxy = iiif2_mod.Proxy(iiif2_mod.GALLICA_BASEURL)
			self.images = []
			# Extract the document identifier			
			docid = iiif2_mod.Proxy.decompose_gallica_ref(self.url)
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
			"metadata": self.metadata,
			"file_path": self.file_path,
			"has_manifest": self.has_manifest,
			"has_iiif_manifest": self.has_iiif_manifest,
			}
		
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


class AudioFrame:
	"""
		A time frame in a video or audio source, along
		with the reference of the related object in the pivot score
	"""
	
	def __init__(self, object_id, begin, end) :
		self.id = object_id
		self.begin = begin
		self.end = end
		
	def to_json (self):
		tframe = {"from" : self.begin, "to": self.end}
		return {"id": self.id,"time_frame": tframe}

	def length(self):
		return self.end - self.begin
	
	def __str__ (self):
		return json.dumps (self.to_json())
	
	@staticmethod
	def from_json (json_dict):
		tframe = json_dict["time_frame"]
		return AudioFrame (json_dict["id"], tframe["from"], tframe["to"])

class AudioManifest:
	"""
		Representation of an internal manifest annotating
		an audio or video source.
		
		The manifest is a list of time frames, each associated
		to an object (typ. a measure) in the pivot srcore
	"""
	
	# Patterns used to generate the ids of objects referred to in frames
	MEASURE_REF_PATTERN = "measure"
	NO_REF_PATTERN = "none"

	def __init__(self, opus_ref, source_ref, ref_pattern="measure") :
		self.opus_ref = opus_ref
		self.source_ref = source_ref
		# List of timeframes
		self.time_frames = []
		# Record the pattern
		self.ref_pattern = ref_pattern

	def rebuild_object_refs(self):
		# This method must be called when the order and number
		# of frames has changed.
		if self.ref_pattern == AudioManifest.MEASURE_REF_PATTERN:
			measure_no = 1
			for tframe in self.time_frames:
				tframe.id = f"m{measure_no}"
				measure_no += 1
		else:
			print ("AudioManifest::rebuild_object_refs. Don't know how to rebuild refs for pattern {self.ref_pattern}")

	def insert_timeframe(self, tframe):
		# Insert a new time frame. 
		# Maybe add some controls
		self.time_frames.append(tframe)
		
	def split_tframe (self, object_id, new_id):
		# Split a time frame in two
		found = False
		pos = 0
		for tframe in self.time_frames:
			if tframe.id == object_id:
				found = True
				#print (f"Found time frame {tframe} at pos {pos}. Split !")
				mid_ts = tframe.begin + tframe.length () / 2
				new_tframe = AudioFrame (new_id, mid_ts, tframe.end)
				tframe.end = mid_ts
				break
			pos += 1
			
		if not found:
			print (f"No such object in the manifest {object_id}.")
		else:
			# Insert in the list
			print (f"Insert {new_tframe} at pos {pos+1}")
			self.time_frames.insert (pos+1, new_tframe)

		# Rebuild the measure refs
		self.rebuild_object_refs()
	
	def merge_tframes (self, object_id, nb_merges=2):
		# Merge a sequence of time frames
		found = False
		pos_target = 0
		for tframe in self.time_frames:
			if tframe.id == object_id:
				found = True
				target = tframe
				#print (f"Found time frame {tframe} at pos {pos_target}. Merge from here !")
				mid_ts = tframe.begin + tframe.length () / 2
				break
			pos_target += 1
			
		if not found:
			print (f"No such object in the manifest {object_id}.")
		else:
			# We know the pos of the target. Get the next nb_merges tframes
			for pos in range (pos_target+1, pos_target + nb_merges):
				merged_frame = self.time_frames[pos]
				target.end = merged_frame.end
				#print (f"Merge {merged_frame} found at pos {pos+1}")
			# Second pass to delete merge frames
			for pos in range (pos_target+1, pos_target + nb_merges):
				del self.time_frames[pos]

		print (f"Result : {target}")
		# Rebuild the measure refs
		self.rebuild_object_refs()

	def load_from_audacity(self, marker_file):
		measure_no = 1
		with open(marker_file) as sync_file:
			synchro_data = csv.reader(sync_file, delimiter='\t')
			current_tstamp = 0
			for synchro in synchro_data:
				tstamp = float (synchro[0])
				if self.ref_pattern == AudioManifest.MEASURE_REF_PATTERN:
					# Follow the measure pattern: "m"+no
					object_ref = f"m{measure_no}"
				else:
					object_ref = ""
					print (f"ERROR: cannot infer the object reference from an Audacity file")
				audio_frame = AudioFrame (object_ref, current_tstamp, tstamp)
				self.insert_timeframe(audio_frame)
				measure_no += 1
				current_tstamp = tstamp

	def load_from_dezrann(self, marker_file):
		with open(marker_file) as sync_file:
			synchros = json.load (sync_file)
		measure_no = 1
		current_tstamp = float(synchros[0]["date"])
		for synchro in synchros[1:]:
			tstamp = float(synchro["date"])
			audio_frame = AudioFrame (f"m{measure_no}", current_tstamp, tstamp)
			self.insert_timeframe(audio_frame)
			measure_no += 1
			current_tstamp = tstamp

	def to_json(self):
		json_frames = []
		for frame in self.time_frames:
			json_frames.append (frame.to_json())
		return {"opus_ref": self.opus_ref, 
					"source_ref": self.source_ref,
					"nb_frames": len(self.time_frames),
					"time_frames": json_frames}

	def show(self):
		print (f"\nAudio manifest for Opus {self.opus_ref} and source {self.source_ref}")
		print (f"Nb time frames {len(self.time_frames)}")
		for tframe in self.time_frames:
			print (f"\tTime frame for object {tframe.id}: {tframe.begin} -- {tframe.end} ")
			
	@staticmethod
	def from_json (json_dict):
		manifest = AudioManifest (json_dict["opus_ref"], json_dict["source_ref"])
		for json_frame in json_dict["time_frames"]:
			tframe = AudioFrame.from_json (json_frame)
			manifest.insert_timeframe(tframe)
		return manifest
	
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
		self.last_music_page = first_p_music
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
		
		# First get the position of the first and last pages in the 
		# image list: this is the first page that contains music
		images_url = []
		for image in images:
			images_url.append(image.url)
		try:
			self.first_music_page = images_url.index (self.pages[0].url) + 1
		except ValueError:
			raise Exception(f"Manifest::add_image_info. Image {self.pages[0].url} is not in the list of Manifest images ")
		try:
			self.last_music_page = images_url.index (self.pages[-1].url) + 1
		except ValueError:
			raise Exception(f"Manifest::add_image_info. Image {self.pages[-1].url} is not in the list of Manifest images ")

		# Next, find the dimension of images		
		for page in self.pages:
			#print (f"Searching for the image of page {page.url}")
			image_found = False
			for img in images:
				if page.url == img.url:
					image_found = True
					page.width = img.width
					page.height = img.height

	def clean_pages_url(self):	
		"""
		  Normalize the IIIF URLs
		"""
		for page in self.pages:
			page.url = iiif2_mod.Proxy.find_page_id(page.url)

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


