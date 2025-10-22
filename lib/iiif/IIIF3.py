
import time
import sys, os
import socket
import argparse
from pathlib import Path

#
# Classes that encapsulate the IIIF Prezi3 implementation
#   Github: https://github.com/iiif-prezi/iiif-prezi3
#   Documentation: https://iiif-prezi.github.io/iiif-prezi3/
#
import iiif_prezi3


class Manifest ():

	'''
		Acts as a proxy for the Prezi3 manifest class
	'''
	
	def __init__(self, id, label) :
		self.prezi_manifest = iiif_prezi3.Manifest(id=id, label={"en":[label]})
		self.prezi_manifest.items = []
	
	def json(self, indent=2):
		return self.prezi_manifest.json(indent)
	
	def add_canvas (self, canvas):
		self.prezi_manifest.items.append (canvas.prezi_canvas)

class Canvas ():
	
	def __init__(self, id, label) :
		self.id = id
		self.prezi_canvas = iiif_prezi3.Canvas (id=id, label={"en":[label]})

	def add_content_list (self, list):
		self.prezi_canvas.add_item (list.prezi_annotation_page)

	def add_annotation_list (self, list):
		self.prezi_canvas.add_annotation (list.prezi_annotation_page)


class AnnotationList():

	def __init__(self, id, label) :
		self.id = id
		self.prezi_annotation_page = iiif_prezi3.AnnotationPage (id=id, label={"en":[label]})

	def add_audio_item (self, annot_id, canvas, audio_uri, format, duration):
		resource = Resource (audio_uri, Annotation.SOUND_TYPE, "audio/mpeg")
		body = ResourceBody (audio_uri, resource)
		body.prezi_body.duration = duration
		body.prezi_body.format = "audio/mpeg"
		canvas.prezi_canvas.duration = duration
	
		annot = Annotation (annot_id, canvas.id, body, Annotation.MOTIVATION_PAINTING)
		self.prezi_annotation_page.add_item (annot.prezi_annotation)

	def add_image_item (self, annot_id, target, image_uri, format, height, width):
		resource = Resource (image_uri, Annotation.IMAGE_TYPE, "image/jpeg")
		body = ResourceBody (image_uri, resource)
		body.prezi_body.height = height
		body.prezi_body.width = width
		body.prezi_body.format = "image/jpeg"
	
		annot = Annotation (annot_id, target, body, Annotation.MOTIVATION_PAINTING)
		self.prezi_annotation_page.add_item (annot.prezi_annotation)

	def add_synchro (self, canvas, uri, content_list_id, polygon, time_frame):
		"""
		    Polygon must be a list of points of the form 1221,1589 2151,1589 1221,2266 2161,2266
		    Time frame is a pair of floats, such as t=0,4.852608
		"""
		body = TextualBody (uri, "resource")
		
		## IMPORTANT: in the Digirati example, the svg patterns featured width, height and 
		##  view box attributes. i did'nt find what it was useful for, but ....
		## investigate in case of problems
		
		svg_pattern = f"<svg xmlns=\"http://www.w3.org/2000/svg\"><polygon points=\"{polygon}\"/></svg>"

		audio_selector = FragmentSelector(FragmentSelector.AUDIO_SELECTOR, time_frame)
		image_selector = FragmentSelector(FragmentSelector.IMAGE_SELECTOR, svg_pattern)
		resource_selector = SpecificResource (content_list_id, [image_selector, audio_selector])
	
		anno = canvas.prezi_canvas.make_annotation(id=uri,
							motivation=Annotation.MOTIVATION_HIGHLIGHTING,
							body=body.get_json_obj(),
							target=resource_selector.get_json_obj(),
							anno_page_id=self.id)

		#self.prezi_annotation_page.add_item (anno)

class Annotation():
		
	MOTIVATION_PAINTING = "painting"
	MOTIVATION_COMMENTING = "commenting"
	MOTIVATION_LINKING = "linking"
	MOTIVATION_QUESTIONING = "questioning"
	MOTIVATION_HIGHLIGHTING = "highlighting"
	
	DATASET_TYPE = "Dataset"
	IMAGE_TYPE = "Image"
	SOUND_TYPE = "Sound"
	TEXT_TYPE = "Text"
	VIDEO_TYPE = "Video"

	def __init__(self, id, target, body, motivation) :
		
		self.id =id
		self.target = target
		self.body = body
		
		# See the enumeration at https://www.w3.org/TR/annotation-model/
		self.motivation = motivation

		self.prezi_annotation = iiif_prezi3.Annotation(id=id,
		 		motivation=motivation, body=body.prezi_body, 
		 		target=target)

class Body:
	'''
	   Represents the body of an annotation, i.e., the sth said 'about' the target.
	   
	   This is a super-class, sub-typed for each type of body
	'''
	
	def __init__(self, id, type):
		self.type = "generic_body"
		self.id = id
		self.prezi_body = iiif_prezi3.AnnotationBody(id=id, type=type)


class TextualBody(Body):
	'''
	   The body value is simply a text
	'''
	
	def __init__(self, id, value) :
		super().__init__(id, Annotation.TEXT_TYPE)
		self.value = value

	def __str__ (self):
		return self.value

	def get_json_obj(self, w3c=True):
		return {"type": "TextualBody", "value": self.value}

class ResourceBody(Body):
	'''
	   The body is a web resource (currently a "specific web resource", described
	   by an URI and a fragment)
	'''
	
	def __init__(self, id, resource) :
		super().__init__(id, resource.type)
		self.resource = resource
		return

	def __str__(self):
		return f"ResourceBody. Source: {self.resource}"

class Resource:
	'''
	  Reference to a resource
	'''

	def __init__(self, id, type, format) :
		self.id = id
		self.type = type
		self.format = format

	def __str__ (self):
		return f"Resource object {self.id}"

class SpecificResource():
	'''
	  Reference to a specific part of a source
	'''
	
	def __init__(self, source, selectors) :
		self.source = source
		self.selectors = selectors

	def __str__ (self):
		return f"Target: {self.source} - {self.selectors}"

	def get_json_obj(self):
		json_selectors = []
		for sel in self.selectors:
			json_selectors.append (sel.get_json_obj())
		return {"type": "SpecificResource", "source": self.source, "selector": json_selectors}

class FragmentSelector:
	'''
	   How to refer to a part of a web resource. 
	 '''
	
	XML_SELECTOR = "http://tools.ietf.org/rfc/rfc3023"
	IMAGE_SELECTOR = "http://www.w3.org/TR/SVG/"
	AUDIO_SELECTOR = "https://www.w3.org/TR/media-frags/"

	def __init__(self, conforms_to, value) :
		# Type of the referred resource: Image, XML, etc.
		if conforms_to == FragmentSelector.IMAGE_SELECTOR:
			self.type = "SvgSelector" 
		else:
			self.type = "FragmentSelector" 
		# To which specification the selector conforms to. Must be one of
		# the selectors given above
		self.conforms_to = conforms_to 
		# The value that specifies the fragment
		self.value = value

	def __str__ (self):
			return f"Fragment selector conform to {self.conforms_to} with value {self.value}"

	def get_json_obj(self):
		''' 
			Return an object for JSON serialisation
		'''
		return {"type": self.type, "conformsTo": self.conforms_to, "value": self.value}

# Defines the conformity of a fragment to a segment selection syntax
FRAGMENT_CONFORMITY = (
    (FragmentSelector.XML_SELECTOR, "An XPointer expression"),
    (FragmentSelector.IMAGE_SELECTOR, "A region in an image"),
	(FragmentSelector.AUDIO_SELECTOR, "A segment in an audio or video document")
)
