'''
 Classes representing annotations on music document elements.
 
 Attempts to closely follow the W3C annotation model (https://www.w3.org/TR/annotation-model/)

'''

import datetime
import json

class Annotation:
	'''
		Represents an annotation
	'''
	
	MOTIVATION_LINKING = "linking"
	MOTIVATION_COMMENTING = "commenting"
	MOTIVATION_QUESTIONING = "questioning"
	
	CATEG_TO_TEXTUAL = "to_textual"
	CATEG_TO_TAXONOMY = "to_annotation_concepts"
	CATEG_TO_IMAGE = "pivot_to_image"
	CATEG_TO_AUDIO = "pivot_to_audio"
	CATEG_TO_VIDEO = "pivot_to_video"
	
	# A counter for generating unique annotation ids
	sequence_ids = 0
	
	@staticmethod
	def get_new_id():
		Annotation.sequence_ids += 1
		return Annotation.sequence_ids


	def __init__(self, creator, target, body, category, 
				annotation_model =  None,
				motivation="linking") :
		self.id = Annotation.get_new_id()
		self.creator = creator 
		self.created = datetime.datetime.now()
		self.modified = datetime.datetime.now()
		
		self.target = target
		self.body = body
		
		# See the enumeration at https://www.w3.org/TR/annotation-model/
		self.motivation = motivation

		# For the record: maybe adding the notion of state would be useful
	
		# Neuma specific part: for usage purposes, we 
		# assign an annotation to a category. One on them is
		# "AnnotationTaxonomy", in which case we also record
		# the annotation model name. The 'body' should then refer
		# to a concept in this model
		# and what is the id of the concept referred to
		self.category = category 
		self.annotation_model = annotation_model
		
	def format_id(self):
		return f'annot{self.id}' 

	def get_json_obj (self):
		''' Produce the JSON string, conform to the W3C spec..'''
		return {"id": self.format_id(), "type": "Annotation", 
			"creator": self.creator.get_json_obj(),
			  "motivation": self.motivation, "category": self.category,
			 "body": self.body.get_json_obj(), "target": self.target.get_json_obj()}

class Body:
	'''
	   Represents the body of an annotation, i.e., the sth said 'about' the target.
	   
	   This is a super-class, sub-typed for each type of body
	'''
	
	def __init__(self, id) :
		self.id = id
		return

	def get_json_obj(self):
		''' 
			Return an object fro JSON serialisation
		'''
		return {"id": self.id}

class TextualBody(Body):
	'''
	   The body value is simply a text
	'''
	
	def __init__(self, id, value) :
		super().__init__(id)
		self.value = value
		return

class ResourceBody(Body):
	'''
	   The body is a web resource (currently a "specific web resource", described
	   by an URI and a fragment)
	'''
	
	def __init__(self, id, resource) :
		super().__init__(id)
		self.resource = resource
		return

class SpecificResource:
	'''
	  Reference to a specific part of a source
	'''
	
		
	XML_MEDIA_FORMAT = "text/xml"

	def __init__(self, source, selector) :
		self.source = source
		self.selector = selector

	def get_json_obj(self):
		''' 
			Return an object for JSON serialisation
		'''
		return {"source": self.source, 
			"selector": self.selector.get_json_obj()}

class FragmentSelector:
	'''
	   How to refer to a part of a web resource. 
	 '''
	
	XML_SELECTOR = "http://tools.ietf.org/rfc/rfc3023"
	MEDIA_SELECTOR = "http://www.w3.org/TR/media-frags/"

	def __init__(self, conforms_to, value) :
		# Type of the referred resource: Image, XML, etc.
		self.type = "FragmentSelector" 
		# To which specification the selector conforms to. Must be one of
		# the selectors given above
		self.conforms_to = conforms_to 
		# The value that specifies the fragment
		self.value = value

	def get_json_obj(self):
		''' 
			Return an object for JSON serialisation
		'''
		return {"type": self.type,
			"type": self.type, "conformsTo": self.conforms_to, "value": self.value}

class Creator:
	'''
	  Entity that creates an annotation
	'''
	
	PERSON_TYPE = "Person"
	SOFTWARE_TYPE = "Software"
	
	def __init__(self, id, type, name) :
		self.id = id
		self.type = type
		self.name = name
		return
	
	def get_json_obj(self):
		return {"id": self.id, "type": self.type, 
			"name": self.name}


	