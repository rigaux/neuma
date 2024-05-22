"""
	A set of classes that provide proxy to Neuma object 
	through REST calls
"""

from neuma_client.exceptions import NotFoundException

from neuma_client.client import NeumaClient, logger

class Collections:
	"""
	Singleton object, the first that must be instantiated. Contains the Rest client
	"""

	def __init__(self, client) :
		self.client = client
		try:
			client.request ("NeumaApi_v3")
			logger.info (f"Connection OK to {client.url()}")
			print (f"Connection OK to {client.url()}")
		except Exception as ex :
			logger.error (f"Unable to connect to {client.url()}: {ex}")

	def get_corpus(self, corpus_ref):
		try:
			res = self.client.request ("Element", full_neuma_ref=corpus_ref)
			return Corpus (self.client, res)
		except:
			raise NotFoundException (f"Corpus not found : {corpus_ref}")
			
class Corpus:

	def __init__(self, client, corpus_dict):		
		self.client = client
		self.ref = corpus_dict["ref"]
		self.title = corpus_dict["title"]
		self.short_title = corpus_dict["short_title"]
		self.description = corpus_dict["description"]
		self.short_description = corpus_dict["short_description"]
		self.parent = corpus_dict["parent"]
		self.composer = corpus_dict["composer"]
		self.licence = corpus_dict["licence"]
		self.copyright= corpus_dict["copyright"]
		
		self.opus_list = []
		self.opus_in_cache = False
		
	def get_opus_list(self):
		"""
			Find the opus in the corpus
		"""
		if not (self.opus_in_cache):
			res = self.client.request ("OpusList", full_neuma_ref=self.ref)
			for op_dict in res['results']:
				self.opus_list.append (Opus(self.client, op_dict))
			self.opus_in_cache = True
		return self.opus_list
	
	def __str__(self):
		return f"Corpus. ref:{self.ref}"

class Opus:

	def __init__(self, client, opus_dict):	
		self.client = client
		self.ref = opus_dict["ref"]	
		self.local_ref = opus_dict["local_ref"]	
		self.title = opus_dict["title"]	

		self.sources_in_cache = False 
		self.sources = []

	def get_sources_list(self):
		"""
			Find the sources in the opus
		"""
		if not (self.sources_in_cache):
			res = self.client.request ("SourceList", full_neuma_ref=self.ref)
			for src_dict in res['results']:
				self.sources .append (Source(self.client, self, src_dict))
			self.sources_in_cache = True
		return self.sources 

	def get_source (self, source_ref):
		if not (self.sources_in_cache):
			self.get_sources_list()
		for src in self.sources:
			if src.ref == source_ref:
				return src
		return None
			
	def source_exists (self, source_ref):
		if not (self.sources_in_cache):
			self.get_sources_list()
			
		for src in self.sources:
			if src.ref == source_ref:
				return True
		return False

class Source:

	IIIF_REF = "iiif"
	
	def __init__(self, client, opus, source_dict):	
		self.client = client
		self.opus = opus
		self.ref = source_dict["ref"]	
		self.url = source_dict["url"]	
		self.description = source_dict["description"]	
		self.source_type = source_dict["source_type"]	
		self.file_path = source_dict["file_path"]	
		self.has_manifest = source_dict["has_manifest"]	
		
		
		self.manifest = None
		self.manifest_in_cache = False
		
		
	def file_url(self):
		if self.file_path is not None:
			return self.client.base_url + self.file_path
		else:
			return None
	
	def __str__(self):
		return f"Source -- {self.opus.ref}/{self.ref}"
	
	"""
	    Part related to the manifest  -- if it exists
	"""
	def get_manifest(self):
		if self.has_manifest == False:
			return None
		
		if  self.manifest_in_cache == False:
			self.manifest  = self.client.request ("SourceManifest", 
											full_neuma_ref=self.opus.ref,
											source_ref=self.ref)
			self.manifest_in_cache = True
		return Manifest(self.manifest)


class Manifest:
	# Description of an IIIF source
	
	def __init__(self, manifest_dict):	
		# The manifest dictionary, obtained from the REST call
		self.manifest_dict  = manifest_dict

	def id_source(self):
		return self.manifest_dict ["id"]
	def url_source(self):
		return self.manifest_dict ["url"]
	
	def nb_pages(self):
		return len (self.manifest_dict["pages"])
	
	def get_page(self, i_page):
		if i_page >= len(self.manifest_dict["pages"]):
			raise Exception ("Attempt to read beyond the number of pages")		
		return self.manifest_dict["pages"][i_page]		
	def page_url (self, i_page):
		page = self.get_page(i_page)
		return page["url"]
	def page_width (self, i_page):
		page = self.get_page(i_page)
		return page["width"]
	def page_height (self, i_page):
		page = self.get_page(i_page)
		return page["height"]
	
	def nb_systems (self, i_page):
		page = self.get_page(i_page)
		return len(page["systems"])

	def first_music_page(self):
		if "first_music_page" in self.manifest_dict.keys():
			return self.manifest_dict["first_music_page"]
		else:
			return 1
	
	def get_system (self, i_page, i_system):
		page = self.get_page(i_page)
		if i_system >= len(page["systems"]):
			raise Exception (f"Attempt to read beyond the number of systems in page {i_page}")
		return page["systems"][i_system]
		
	def nb_staves(self, i_page, i_system):
		system = self.get_system(i_page, i_system)
		return len(system["staves"])
		
	def system_region(self, i_page, i_system):
		system = self.get_system(i_page, i_system)
		return system["region"]

	def nb_measures(self, i_page, i_system):
		system = self.get_system(i_page, i_system)
		if "measures" in system.keys():
			return len(system["measures"])
		else:
			raise Exception ("No 'measures' field in the manifest. Probably an obsolete version")		

	def get_measure(self, i_page, i_system, i_measure):
		system = self.get_system(i_page, i_system)
		if i_measure >= len(system["measures"]):
			raise Exception (f"Attempt to read beyond the number of measures in system {i_system}")
		return system["measures"][i_measure]
			
