

'''
 A class used to represent the metadata of an Opus
'''
from _weakref import ref

class OpusSource:
	'''
		A source (digital document referring to an Opus
	'''
	def __init__(self, ref, source_type, mime_type, url):
		self.ref = ref
		self.source_type = source_type
		self.mime_type = mime_type
		self.url  = url
		
class OpusMeta:
	'''
		A general utility class to manage JSON LD specifics
	'''
	
	def __init__(self, ref, title, composer):
		self.ref = ref
		self.title = title
		self.composer = composer
		self.sources = []

	def add_source (self, source):
		'''
		  Add a source to the opus
		'''
		self.sources.append(source)
		
	def to_json (self):
		return {"ref": self.ref,
				"title": self.title,
				"composer": self.composer,
				"sources": self.sources
				}
	
