
from lib.music.jsonld import JsonLD

import lib.music.Score as score_mod

'''
 A class used to represent the metadata of an Opus
'''


class OpusFile:
	'''
		Just a URL for the time being
	'''
	def __init__(self, name, url):
		self.name = name
		self.url = url
		
	def to_json (self):
		return {"name": self.name, "url": self.url}


class OpusFeature:
	'''
		A feature = a key value pair
	'''
	def __init__(self, key, value):
		self.key = key
		self.value = value
		
	def to_json (self):
		return {"feature_key": self.key, "feature_value": self.value}

class OpusMeta:
	'''
		Serializable representation of an Opus
	'''
	
	def __init__(self, corpus_ref, local_ref, title, composer, id=None):
		self.id = id 
		
		self.local_ref = local_ref
		self.ref = corpus_ref + ":" + local_ref
		self.corpus_ref = corpus_ref
		self.title = title
		self.composer = composer
		self.sources = []
		self.features = []
		self.files = []

	def add_source (self, source):
		self.sources.append(source)	
	def add_feature (self, feature):
		self.features.append(feature)
	def add_file (self, the_file):
		self.files.append(the_file)

	def to_json (self):
		# 
		features =[]
		for f in self.features:
			features.append(f.to_json())
		sources =[]
		for s in self.sources:
			sources.append(s.to_json())
		files =[]
		for f in self.files:
			files.append(f.to_json())

		if self.id is not None:
			# Adding the DB id. Useful for REST services that want to 
			# directly require and opus
			opus_dict = {"db_id": self.id}
		else:
			opus_dict = {}
		opus_dict["ref"] =  self.ref
		opus_dict["local_ref"] = self.local_ref
		opus_dict["corpus_ref"] = self.corpus_ref
		opus_dict["title"] = self.title
		opus_dict["composer"] = self.composer
		opus_dict["features"] =  features
		opus_dict["sources"] = sources
		opus_dict["files"] = files
		
		return opus_dict

	def to_jsonld(self):
		ontos = {"scorelib": JsonLD.SCORELIB_ONTOLOGY_URI}
		jsonld = JsonLD (ontos)
		
		jsonld.add_type("scorelib", "Opus")
		jsonld.add_type("scorelib", "Score")
		jsonld.add_type("scorelib", "Source")
		

		opus_dict = {"@id": self.ref, 
			     "@type": "Opus",
				"hasOpusTitle": self.title,
				}
		
		features =[]
		for f in self.features:
			features.append(f.to_json())
		if len(features) > 0:
			opus_dict["hasFeature"] = features
		sources =[]
		for s in self.sources:
			sources.append(s.to_json())
		if len(sources) > 0:
			opus_dict["hasSource"] = sources

		if self.composer is not None: 
			opus_dict["hasAuthor"] = self.composer
			
		''' If values are managed as meta data later 
		for meta in self.get_metas ():
			if meta.meta_key == OpusMeta.MK_COMPOSER:
				dict["hasAuthor"] = meta.meta_value
		'''

		for f in self.files:
			opus_dict["hasScore"] = {"@type": "Score", 
							    "@id": f.name,
							    "uri": f.url
							    }
		return jsonld.get_context() | opus_dict
