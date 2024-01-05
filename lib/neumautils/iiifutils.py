
# import the logging library
import logging
import json
import requests

# Get an instance of a logger
# See https://realpython.com/python-logging/

#logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# Create file handler
f_handler = logging.FileHandler(__name__ + '.log')
f_handler.setLevel(logging.WARNING)
# Create formatters and add it to handlers
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
# Add handlers to the logger
logger.addHandler(f_handler)

# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.WARNING)
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
#logger.addHandler(c_handler)

def set_logging_level(level):
	logger.setLevel(level)
			
GALLICA_BASEURL = 'https://gallica.bnf.fr/iiif/ark:/'
GALLICA_UI_BASEURL = 'https://gallica.bnf.fr/ark:/'

class Proxy:
	"""
		A IIIF services wrapper
	"""
	def __init__(self, base_url=None):
		
		if base_url == None:
			# Gallica server by default
			self.base_url = GALLICA_BASEURL
		else:
			self.base_url = base_url
		
	def get_document (self, identifier):
		return Document (identifier)

class Document:
	
	def __init__(self, identifier):
		self.id = identifier
		
		# Try to get the manifest
		req_url = "".join([GALLICA_BASEURL, self.id, '/manifest.json'])
		r = requests.get(req_url)
		r.raise_for_status()
		self.manifest = r.json()
		
		# Nb of canvases. We assume a simple document whith only one sequence
		self.nb_canvases = len (self.manifest["sequences"][0]["canvases"])
	
	def get_canvas (self, i_canvas):
		if i_canvas < 0 or i_canvas >= self.nb_canvases:
			logger.error (f"Attempt to access a canvas beyond range: {i_canvas} ")
		return Canvas (self.manifest["sequences"][0]["canvases"][i_canvas])
		
class Canvas:
	
	def __init__(self, canvas_dict):
		self.value = canvas_dict
		self.nb_images = len (self.value["images"])
	def id(self):
		return self.value["@id"]
	
	def get_image(self, i_img):
		if i_img < 0 or i_img >= self.nb_images:
			logger.error (f"Attempt to access an image beyond range: {i_img} ")
		return Image (self.value["images"][i_img])
	
class Image:
	
	def __init__(self, img_dict):
		res =  img_dict["resource"]
		self.format = res["format"]
		print (f"Init image id = {res['@id']}")
		self.url = res["@id"]
		self.width = res["width"]
		self.height = res["height"]
		
	def to_dict(self):
		return {"format": self.format, "width": self.width, "height": self.height,
			  "url": self.url}
		
	def id(self):
		return self.value["@id"]