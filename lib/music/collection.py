
import json

from lib.music.jsonld import JsonLD
import lib.music.Score as score_mod

####
#
#  DB-independent classes to represent the equivalent of Corpus/Opus
#  hierarchies without being tied to the DB
#
#  Called Collection and CollectionItem for clarity
####


class Collection:
	'''
		A collection of items
	'''
	
	def __init__(self, url, ref, title, short_title,
				description, short_description, is_public,
				composer, licence, copyright, supervisors,
				thumbnail):
				
		self.url = url
		self.ref = ref
		self.local_ref =  local_ref(ref)
		self.title = title
		self.short_title = title
		self.composer = composer
		self.description = description
		self.short_description = short_description
		self.is_public = is_public
		if licence is not None:
			self.licence = licence.to_dict()
		else:
			self.licence = None
		if thumbnail is not None:
			self.thumbnail = thumbnail.to_dict()
		else:
			self.thumbnail = None
		self.copyright = copyright
		self.supervisors = supervisors

	def to_dict(self):
		core = {"ref": self.ref, 
				"local_ref": self.local_ref, 
				"url": self.url,
				"title": self.title, 
				"short_title": self.short_title, 
				"description": self.description, 
				"short_description": self.short_description,
				"is_public": self.is_public,
				"copyright": self.copyright,
				"supervisors": self.supervisors
		}
		if self.licence is not None:
			core["licence"] = self.licence
		if self.composer is not None:
			core["composer"] = self.composer.to_json()
		return core

	def json(self, indent=2):
		return json.dumps (self.to_dict(), indent=indent)

def local_ref(ref):
	"""
		Last part of a Neuma ID
"""
	last_pos = ref.rfind(":")
	return ref[last_pos+1:]
