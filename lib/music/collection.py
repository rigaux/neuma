
import json

from lib.music.jsonld import JsonLD
import lib.music.Score as score_mod
import lib.music.source as source_mod

####
#
#  DB-independent classes to represent the equivalent of Corpus/Opus
#  hierarchies without being tied to the DB
#
#  Called Collection and CollectionItem for clarity
####


class Collection:
	FROM_OBJECT="from_obj"
	FROM_DICT="from_dict"
	
	'''
		A collection of items (eq. to a Corpus in Neuma)
	'''
	
	def __init__(self, url, ref, title, short_title,
				description, short_description, is_public,
				composer, licence, copyright, supervisors,
				thumbnail, organization, mode=FROM_OBJECT):
				
		self.url = url
		self.ref = ref
		self.local_ref =  local_ref(ref)
		self.title = title
		self.short_title = title
		if composer is not None:
			if mode == Collection.FROM_OBJECT:
				self.composer = composer.to_dict()
			else:
				self.composer = composer
		else:
			self.composer = None
		self.description = description
		self.short_description = short_description
		self.is_public = is_public
		if licence is not None:
			if mode == Collection.FROM_OBJECT:
				self.licence = licence.to_dict()
			else:
				self.licence = licence
		else:
			self.licence = None
		if thumbnail is not None:
			if mode == Collection.FROM_OBJECT:
				self.thumbnail = thumbnail.to_dict()
			else:
				self.thumbnail = thumbnail
		else:
			self.thumbnail = None
		if organization is not None:
			if mode == Collection.FROM_OBJECT:
				self.organization = organization.to_dict()
			else:
				self.organization = organization
		else:
			self.organization = None
		self.copyright = copyright
		self.supervisors = supervisors

	def to_dict(self):
		return {"ref": self.ref, 
				"local_ref": self.local_ref, 
				"url": self.url,
				"title": self.title, 
				"short_title": self.short_title, 
				"description": self.description, 
				"short_description": self.short_description,
				"is_public": self.is_public,
				"copyright": self.copyright,
				"supervisors": self.supervisors,
				"organization": self.organization,
				"licence":  self.licence,
				"thumbnail":  self.thumbnail,
				"composer": self.composer
		}

	@staticmethod
	def from_dict(dict_col):
		"""Load content from a dictionary."""
		return Collection(dict_col["url"], dict_col["ref"], 
					dict_col["title"], dict_col["short_title"],
					dict_col["description"], dict_col["short_description"],
					dict_col["is_public"], dict_col["composer"],
					dict_col["licence"],  dict_col["copyright"],
					dict_col["supervisors"], dict_col["thumbnail"],
					dict_col["organization"], Collection.FROM_DICT)
					

	def json(self, indent=2):
		return json.dumps (self.to_dict(), ensure_ascii=False, indent=indent)

class CollectionItem:
	'''
		A collection item (eq. to an Opus in Neuma)
	'''
	#FROM_OBJECT="from_obj"
	#FROM_DICT="from_dict"

	def __init__(self, url, collection_ref, ref, 
				title, composer, description,
				metadata, features, mode=Collection.FROM_OBJECT):
		self.url = url
		self.ref = ref
		self.local_ref =  local_ref(ref)
		self.title = title
		self.collection_ref = collection_ref
		if composer is not None:
			if mode == Collection.FROM_OBJECT:
				self.composer = composer.to_dict()
			else:
				self.composer = composer
		else:
			self.composer = None
		self.description = description
		self.sources = []
		self.metadata = metadata
		self.features = features
		self.files = []

	def add_source (self, source):
		self.sources.append(source)	
	def add_file (self, the_file):
		self.files.append(the_file)

	def to_dict (self):
		item = {"id": self.url, # Historical
				"url": self.url, "ref": self.ref, 
				"local_ref": self.local_ref, 
				"collection_ref": self.collection_ref,
				"title": self.title, 
				"description": self.description,
				"composer": self.composer,
				"metadata": self.metadata}

		item["features"] =[]
		for f in self.features:
			item["features"].append(f.to_dict())
		item["sources"] =[]
		for s in self.sources:
			item["sources"].append(s.to_dict())
		item["files"] =[]
		for f in self.files:
			item["files"].append(f.to_dict())
		return item

	@staticmethod
	def from_dict(dict_opus):
		"""Load content from a dictionary."""
		
		# Historical
		if "url" not in dict_opus:
			dict_opus["url"] = dict_opus["id"]
		if "metadata" not in dict_opus:
			dict_opus["metadata"] = []
		###
		
		item = CollectionItem(dict_opus["url"], 
							dict_opus["collection_ref"],
							dict_opus["ref"],
							dict_opus["title"],
							dict_opus["composer"],
							dict_opus["description"],
							dict_opus["metadata"],
							dict_opus["features"],
							Collection.FROM_DICT)
		for source_dict in dict_opus["sources"]:
			item_source = source_mod.ItemSource.from_dict (source_dict)
			item.add_source (item_source)
		return item
		
	def json(self, indent=2):
		return json.dumps (self.to_dict(), ensure_ascii=False, indent=indent)

def local_ref(ref):
	"""
		Last part of a Neuma ID
"""
	last_pos = ref.rfind(":")
	return ref[last_pos+1:]
