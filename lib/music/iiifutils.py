
import json
import requests

from urllib.parse import urljoin, urlparse
from pathlib import Path, PurePath

			
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

	@staticmethod
	def decompose_gallica_ref (iiif_url):
		split_url = iiif_url.split(GALLICA_UI_BASEURL, 1)
		if split_url is not None and len(split_url) > 0:
			return split_url[1]
		else:
			raise score_mod.CScoreModelError (f"Invalid Gallica IIIF reference: {iiif_url}")
		
	@staticmethod
	def find_page_ref(iiif_url):
		# Attempt to get the page reference from the URL
		split_url = urlparse(iiif_url)
		if len(PurePath(split_url.path).parts) > 5:
			page_ref = PurePath(split_url.path).parts[5]
		else: 
			page_ref = PurePath(split_url.path).stem
		return page_ref

	@staticmethod
	def find_page_id(iiif_url):
		# Attempt to get the IIIF page reference from the URL,
		# by eliminating IIIF  extraction instructions
		split_url = urlparse(iiif_url)
		if len(PurePath(split_url.path).parts) > 5:
			# Get rid of all arguments beyond 5
			clean_url = split_url.scheme + "://" + split_url.hostname
			for i in [1, 2, 3, 4, 5]:
				clean_url = clean_url +  '/' +  PurePath(split_url.path).parts[i]  
			return clean_url
		else: 
			# The URL is already the correct ID
			return iiif_url 

class Document:
	
	def __init__(self, manifest):
		self.manifest = manifest
		
		# Nb of canvases. We assume a simple document whith only one sequence
		self.nb_canvases = len (self.manifest["sequences"][0]["canvases"])
	
	def get_canvas (self, i_canvas):
		if i_canvas < 0 or i_canvas >= self.nb_canvases:
			print(f"Attempt to access a canvas beyond range: {i_canvas} ")
		return Canvas (self.manifest["sequences"][0]["canvases"][i_canvas])

	def get_images(self):
		images = []		
		for i in range(self.nb_canvases):
			canvas = self.get_canvas(i)
			images.append(canvas.get_image(0))
		return images

class Canvas:
	
	def __init__(self, canvas_dict):
		self.value = canvas_dict
		self.nb_images = len (self.value["images"])
	def id(self):
		return self.value["@id"]
	
	def get_image(self, i_img):
		if i_img < 0 or i_img >= self.nb_images:
			print (f"Attempt to access an image beyond range: {i_img} ")
		return Image (self.value["images"][i_img])
	
class Image:
	
	def __init__(self, img_dict):
		res =  img_dict["resource"]
		self.format = res["format"]
		self.url = res["service"]["@id"]
		self.width = res["width"]
		self.height = res["height"]
		
	def to_dict(self):
		return {"format": self.format, "width": self.width, "height": self.height,
			  "url": self.url}
		
	def id(self):
		return self.value["@id"]