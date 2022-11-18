'''
 Classes representing annotations on music document elements.
 
 Attempts to closely follow the W3C annotation model (https://www.w3.org/TR/annotation-model/)

'''


import datetime
from .constants import *


class Annotation:
	'''
		Represents an annotation
	'''
	
	MOTIVATION_LINKING = "linking"
	MOTIVATION_COMMENTING = "commenting"
	MOTIVATION_QUESTIONING = "questioning"
	
	# List of target classes
	TC_MEASURE = "measure"
	TC_NOTE = "note"

	# A counter for generating unique annotation ids
	sequence_ids = 0
	
	@staticmethod
	def get_new_id():
		Annotation.sequence_ids += 1
		return Annotation.sequence_ids


	def __init__(self, id, creator, target, body, 
				annotation_model,
				annotation_concept,
				motivation,
				created, modified) :
		
		self.id =id
		self.creator = creator 
		self.created = created
		self.modified = modified
		
		self.target = target
		self.body = body
		
		# See the enumeration at https://www.w3.org/TR/annotation-model/
		self.motivation = motivation

		# For the record: maybe adding the notion of state would be useful
	
		# Neuma specific part: for usage purposes, we 
		# assign an annotation to a concept in an annotation model.
		self.annotation_model = annotation_model
		self.annotation_concept = annotation_concept
		# Default style
		self.style = Style ("square", "content6")
		
	def format_id(self):
		return f'annot{self.id}' 

	def get_json_obj (self):
		''' Produce the JSON string, conform to the W3C spec..'''
		return {"id": self.id, "type": "Annotation", 
			"creator": self.creator.get_json_obj(),
			  "motivation": self.motivation, "annotation_model": self.annotation_model,
			  "annotation_concept": self.annotation_concept,
			 "body": self.body.get_json_obj(), 
			 "target": self.target.get_json_obj(),
			 "style": self.style.get_json_obj(),
			 "created": str(self.created),
			 "modified": str(self.modified)}
		
	def set_style (self, style):
		self.style = style

	@staticmethod 
	def create_target_for_annotation(doc_url, xml_id):
		''' 
			Create the target component for an XML fragment
		'''
		target_selector = FragmentSelector(FragmentSelector.XML_SELECTOR, xml_id)
		target_resource = SpecificResource(doc_url, target_selector)
		return Target(target_resource)
		

	@staticmethod 
	def create_annot_from_xml_to_image(creator, doc_url, xml_id, image_url, region, annot_concept):
		''' 
			An annotation that links an XML element to an image region
		'''
		target = Annotation.create_target_for_annotation(doc_url, xml_id)
		
		body_selector = FragmentSelector(FragmentSelector.IMAGE_SELECTOR, region)
		body_resource = SpecificResource(image_url, body_selector)
		body = ResourceBody(body_resource)
		return Annotation(Annotation.get_new_id(), creator, target, body, 
							AM_IMAGE_REGION, annot_concept, 
							Annotation.MOTIVATION_LINKING,
							datetime.datetime.now(), datetime.datetime.now())

	@staticmethod 
	def create_annot_from_error (creator, doc_url, xml_id, message, annot_concept):
		''' 
			An annotation that links an XML element to an image region
		'''
		target = Annotation.create_target_for_annotation(doc_url, xml_id)
		body = TextualBody(message)
		return Annotation(Annotation.get_new_id(), creator, target, body, 
							AM_OMR_ERROR, annot_concept, 
							Annotation.MOTIVATION_QUESTIONING,
							datetime.datetime.now(), datetime.datetime.now())

# Define the restricted list of possible motivations
MOTIVATION_OPTIONS = (
    (Annotation.MOTIVATION_LINKING, "Linking sources"),
    (Annotation.MOTIVATION_COMMENTING, "Commenting a target"),
    (Annotation.MOTIVATION_QUESTIONING, "Questioning a target"),
)
# Define the restricted list of possible target classes
TARGET_CLASSES = (
    (Annotation.TC_MEASURE, "Annotates a measure in a score"),
    (Annotation.TC_NOTE, "Annotates a note in a score")
)


class Target:
	'''
	   Represents the target of an annotation. Currently, only supported: 
	   resource fragment (aka specific resource)
	'''
	
	def __init__(self, resource) :
		# If the annotation itself has a URI, it may be given
		self.resource = resource
		return

	def get_json_obj(self):
		return {"resource": self.resource.get_json_obj(), "type": "SpecificResource"}

class Body:
	'''
	   Represents the body of an annotation, i.e., the sth said 'about' the target.
	   
	   This is a super-class, sub-typed for each type of body
	'''
	
	def __init__(self):
		self.type = "generic_body"
		
	def get_json_obj(self):
		''' 
			Return an object from JSON serialisation
		'''
		return {"type": self.type}

class TextualBody(Body):
	'''
	   The body value is simply a text
	'''
	
	def __init__(self,  value) :
		self.type = "textual_body"
		self.value = value
		return

	def get_json_obj(self):
		return {"type": "TextualBody", "value": self.value}

class ResourceBody(Body):
	'''
	   The body is a web resource (currently a "specific web resource", described
	   by an URI and a fragment)
	'''
	
	def __init__(self, resource) :
		self.type = "resource_body"
		self.resource = resource
		return

	def get_json_obj(self):
		return {"type": "SpecificResource", 
			"resource": self.resource.get_json_obj()}

class Style:
	'''
	   Some instructions to display an annotation
	'''
	
	def __init__(self, icon, color) :
		# If the annotation itself has a URI, it may be given
		self.icon = icon
		self.color = color

	def get_json_obj(self):
		return {"icon": self.icon, "color": self.color}

##########  Resources and resources fragment description
class Resource:
	'''
	  Reference to a resource
	'''
	

	def __init__(self, source) :
		self.source = source

	def get_json_obj(self):
		return {"source": self.source}

class SpecificResource(Resource):
	'''
	  Reference to a specific part of a source
	'''
	
	def __init__(self, source, selector) :
		super().__init__(source)
		self.selector = selector

	def get_json_obj(self):
		return {"source": self.source, 
			"selector": self.selector.get_json_obj()}

class FragmentSelector:
	'''
	   How to refer to a part of a web resource. 
	 '''
	
	XML_SELECTOR = "http://tools.ietf.org/rfc/rfc3023"
	IMAGE_SELECTOR = "https://www.w3.org/TR/media-frags/#naming-space"
	AUDIO_SELECTOR = "https://www.w3.org/TR/media-frags/#naming-time"


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

# Defines the conformity of a fragment to a segment selection syntax
FRAGMENT_CONFORMITY = (
    (FragmentSelector.XML_SELECTOR, "An XPointer expression"),
    (FragmentSelector.IMAGE_SELECTOR, "A region in an image"),
	(FragmentSelector.AUDIO_SELECTOR, "A segment in an audio or video document")
)

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


	