
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

class Property ():
	'''
		IIIF property model: A dict of arrays of strings, 
		  each item key being the language code
	'''
	
	def __init__(self,  strings, lang="fr") :
		self.lang = lang
		# Must be an array
		if isinstance(strings, str):
			# We received a single string
			self.strings = [strings]
		else:
			self.strings = strings
	
	def to_dict(self):
		return {self.lang : self.strings}

	@staticmethod 
	def from_dict(prop_dict):
		for key, vals in prop_dict.items():
			return Property (vals, key)
			# We ignore multiple languages...
	
class Metadata ():
	'''
		IIIF metadata model: a label/value pair, each being a property
	'''
	
	def __init__(self, label, value) :
		self.label = label
		self.value = value
	
	def to_dict(self):
		return {"label": self.label.to_dict(),
				"value" : self.value.to_dict()}

class Homepage ():
	'''
		IIIF homepagae model
	'''
	
	def __init__(self, id, label) :
		self.prezi_homepage = iiif_prezi3.Homepage(id=id, 
					label=label.to_dict(), type="Text",
					format="text/html")

class Provider ():

	'''
		IIIF provider https://iiif.io/api/presentation/3.0/#provider
	'''
	
	def __init__(self, id, label, homepage=None, logo=None) :
		self.homepage = homepage
		self.logo = logo
		self.prezi_provider = iiif_prezi3.Provider(id=id, 
					label=label.to_dict(), 
					homepage=homepage.prezi_homepage)
		if logo is not None:
			self.prezi_provider.logo = logo.prezi_body

class Collection ():

	'''
		Acts as a proxy for the Prezi3 collection class
	'''
	
	def __init__(self, id, label) :
		self.id = id
		self.prezi_collection = iiif_prezi3.Collection(id=id, 
					label=label.to_dict())
		self.prezi_collection.items = []
		self.prezi_collection.metadata = []
	
	def json(self, indent=2):
		return self.prezi_collection.json(indent)

	def set_label (self, label):
		self.prezi_collection.label = label.to_dict()
	def set_summary (self, summary):
		self.prezi_collection.summary = summary.to_dict()
	def add_metadata (self, metadata):
		self.prezi_collection.metadata.append(metadata.to_dict())
	def set_rights (self, licence):
		self.prezi_collection.rights = licence
		
	def set_thumbnail (self, thumbnail):
		self.prezi_collection.thumbnail = thumbnail.prezi_body
		
	def set_provider (self, provider):
		self.prezi_collection.provider = provider.prezi_provider
				
	def set_required_statement(self, required_stmt):
		self.prezi_collection.requiredStatement = required_stmt.to_dict()

	def add_manifest_ref (self,  manifest_ref):
		self.prezi_collection.items.append(manifest_ref.prezi_manifest)

class ManifestRef ():
	'''
		A reference to a manifest, with and id, label and a thumbnail
	'''
	
	def __init__(self, id, label, thumbnail) :
		label_prop = Property (label)
		self.prezi_manifest = iiif_prezi3.ManifestRef(id=id, 
					label=label_prop.to_dict(), 
					thumbnail=thumbnail.prezi_body)

class Manifest ():

	'''
		Acts as a proxy for the Prezi3 manifest class
	'''
	
	def __init__(self, id, label) :
		self.id = id
		#List of Canvas objects
		self.canvases = []
		
		# Parallel prezi structure. never shown !
		self.prezi_manifest = iiif_prezi3.Manifest(id=id, 
					label=label.to_dict())
		self.prezi_manifest.items = []
		self.prezi_manifest.metadata = []
	
	def json(self, indent=2):
		return self.prezi_manifest.json(indent)
	
	def add_canvas (self, canvas):
		self.prezi_manifest.items.append (canvas.prezi_canvas)

	# Accessors
	def get_canvases (self):
		return self.canvases
		

	# Update methods
	def set_label (self, label):
		self.prezi_manifest.label = label.to_dict()
	def set_summary (self, summary):
		self.prezi_manifest.summary = summary.to_dict()
	def set_rights (self, licence):
		self.prezi_manifest.rights = licence
	def set_thumbnail (self, thumbnail):
		self.prezi_manifest.thumbnail = thumbnail.prezi_body
	def set_provider (self, provider):
		self.prezi_manifest.provider = provider.prezi_provider	
	def set_required_statement(self, required_stmt):
		self.prezi_manifest.requiredStatement = required_stmt.to_dict()
	def add_metadata (self, metadata):
		self.prezi_manifest.metadata.append(metadata.to_dict())

	@staticmethod
	def load_from_dict(manifest_dict):
		label = Property.from_dict(manifest_dict["label"])
		manifest = Manifest (id=manifest_dict["id"],
							label=label)
		# Load the prezi manifest from the unpacked dictionnary
		manifest.prezi_manifest = iiif_prezi3.Manifest(**manifest_dict)

		# Feed the proxy structure from the Prezi one
		for item in manifest.prezi_manifest.items:
			if item.type == "Canvas":
				canvas = Canvas.load_from_dict(item)
				manifest.canvases.append(canvas)

		return manifest

class Canvas ():
	
	def __init__(self, id, label) :
		self.id = id
		self.annotations_lists = []
		self.contents_lists = []
		self.prezi_canvas = iiif_prezi3.Canvas (id=id, 
								label=label.to_dict())
			
	# A content is a reference to a media 
	def add_content_list (self, list):
		self.prezi_canvas.add_item (list.prezi_annotation_page)

	# Annotations add infos on contents
	def add_annotation_list (self, list):
		self.prezi_canvas.add_annotation (list.prezi_annotation_page)
	
		# Accessors
	def get_content_lists (self):
		return self.contents_lists

	@staticmethod 
	def load_from_dict(prezi_item):
		label = Property.from_dict(prezi_item.label)
		canvas = Canvas (id=prezi_item.id, label=label)
		canvas.prezi_canvas = prezi_item
		
		# Load content pages (found in the sub-items list)
		for a in canvas.prezi_canvas.items:
			if a.type == "AnnotationPage":
				content_list = AnnotationList.load_from_dict(a)
				content_list.prezi_annotation_page = a
				canvas.contents_lists.append(content_list)

		# We should load annotations as well (found in the sub-annotations 
		# list)). TO DO
		return canvas

class AnnotationList():

	def __init__(self, id) :
		self.id = id
		self.annotations = []
		self.prezi_annotation_page = iiif_prezi3.AnnotationPage (id=id)

	@staticmethod 
	def load_from_dict(prezi_annot_list):
		alist = AnnotationList(id=prezi_annot_list.id)
		alist.prezi_annotation_page = prezi_annot_list
		alist.load_annotations()
		return alist
		
	def load_annotations (self, motivation="painting"):
		# Load annotations
		for prezi_annot in self.prezi_annotation_page.items:
			print (f"Motivation {prezi_annot.motivation}")
			if prezi_annot.motivation == motivation:
				body = Body.load_from_dict (prezi_annot.body)
				annot = Annotation (prezi_annot.id, 
								prezi_annot.target, 
								body,
								prezi_annot.motivation) 
				self.annotations.append(annot)
		return self.annotations
	
	def add_audio_item (self, annot_id, annot_type, canvas, audio_uri, format, 
							duration):
							
		resource = Resource (audio_uri, annot_type, format)
		body = ResourceBody (audio_uri, resource)
		body.prezi_body.duration = duration
		body.prezi_body.format = format
		canvas.prezi_canvas.duration = duration
		
		annot = Annotation (annot_id, canvas.id, body, 
					Annotation.MOTIVATION_PAINTING)
		self.prezi_annotation_page.add_item (annot.prezi_annotation)
		return annot

	def add_image_item (self, annot_id, target, image_uri, format, 
				height, width, label, summary):
		resource = Resource (image_uri, Annotation.IMAGE_TYPE, "image/jpeg")
		body = ResourceBody (image_uri, resource)
		body.prezi_body.height = height
		body.prezi_body.width = width
		body.prezi_body.format = "image/jpeg"
	
		annot = Annotation (annot_id, target, body, 
				Annotation.MOTIVATION_PAINTING)
		self.prezi_annotation_page.add_item (annot.prezi_annotation)
		return annot

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

	def __init__(self, id, target, body, motivation, 
						label=None) :
		
		self.id =id
		self.target = target
		self.body = body
		
		# See the enumeration at https://www.w3.org/TR/annotation-model/
		self.motivation = motivation

		self.prezi_annotation = iiif_prezi3.Annotation(id=id,
		 		motivation=motivation, body=body.prezi_body, 
		 		target=target)
			
	def set_label (self, label):
		self.prezi_annotation.label = label.to_dict()
	def set_summary (self, summary):
		self.prezi_annotation.summary = summary.to_dict()
	def set_rights (self, licence):
		self.prezi_annotation.rights = licence
	def set_thumbnail (self, thumbnail):
		self.prezi_annotation.thumbnail = thumbnail.prezi_body
	def set_provider (self, provider):
		self.prezi_annotation.provider = provider.prezi_provider	
	def set_required_statement(self, required_stmt):
		self.prezi_annotation.requiredStatement = required_stmt.to_dict()

class Body:
	'''
	   Represents the body of an annotation, i.e., the sth said 'about' the target.
	   
	   This is a super-class, sub-typed for each type of body
	'''
	
	def __init__(self, id, type):
		self.type = "generic_body"
		self.id = id
		self.prezi_body = iiif_prezi3.AnnotationBody(id=id, type=type)

	@staticmethod
	def load_from_dict(prezi_body):
		body =  Body (id=prezi_body.id, type=prezi_body.type)
		body.prezi_body = prezi_body
		return body
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

class ImageBody(Body):
	'''
	   An annotation body with a width and heigy
	'''
	
	def __init__(self, id, width, height, service=None) :
		super().__init__(id, Annotation.IMAGE_TYPE)
		self.prezi_body.width=width
		self.prezi_body.height=height
		self.prezi_body.format="image/jpeg"
		if service is not None:
			# Add the service ref
			self.prezi_body.service = {"id": service, "type": "ImageService3"}

	def __str__ (self):
		return self.id

	def to_dict(self):
		return self.prezi_body

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
