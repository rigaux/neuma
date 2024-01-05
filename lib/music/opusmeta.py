
from lib.music.jsonld import JsonLD

import lib.music.Score as score_mod

import lib.neumautils.iiifutils as iiif_mod

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


class OpusSource:
	'''
		A source (digital document referring to an Opus
	'''
	
	# Codes for normalized references
	DMOS_REF = "dmos"
	MEI_REF = "ref_mei"
	IIIF_REF = "gallica"
	
	def __init__(self, ref, source_type, mime_type, url):
		self.ref = ref
		self.source_type = source_type
		self.mime_type = mime_type
		self.url  = url
		self.description = ""

		# IIIF extraction: only for sources of type IIIF_REF
		if self.ref == self.IIIF_REF:
			iiif_proxy = iiif_mod.Proxy(iiif_mod.GALLICA_BASEURL)
			self.images = []
			# Extract the document identifier			
			docid = OpusSource.extract_iiif_id(self.url)
			try:
				document = iiif_proxy.get_document(docid)
				for i in range(document.nb_canvases):
					canvas = document.get_canvas(i)
					self.images.append(canvas.get_image(0))
			except Exception as ex:
				score_mod.logger.info(str(ex))
		
	@staticmethod
	def extract_iiif_id (iiif_url):
		split_url = iiif_url.split(iiif_mod.GALLICA_UI_BASEURL, 1)
		if split_url is not None and len(split_url) > 0:
			return split_url[1]
		else:
			raise score_mod.CScoreModelError (f"Invalid Gallica IIIF reference: {iiif_url}")
		
	def to_json (self):
		source_dict =  {
			"ref": self.ref, 
			"description": self.description,
			"source_type": self.source_type, 
			"mime_type": self.mime_type, 
			"url": self.url}
		
		if self.ref == self.IIIF_REF:
			source_dict["images"] = []
			for img in self.images:
				source_dict["images"].append(img.to_dict())
		return source_dict

class OpusMeta:
	'''
		Serializable representation of an Opus
	'''
	
	def __init__(self, ref, title, composer):
		self.ref = ref
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
		return {"ref": self.ref,
				"title": self.title,
				"composer": self.composer,
				"features": features,
				"sources": sources,
				"files": files
				}
	
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
