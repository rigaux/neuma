from rest_framework import serializers

# Modèles
from manager.models import (
	Corpus,
	Opus,
	AnalyticModel,
	AnalyticConcept,
	Annotation,
	Upload,
	OpusSource,
	SourceType
)

# Types sent from the ArkIndex API
SCORE_TYPE = "Score"
PAGE_TYPE = "ScorePage"


"""
  For simple services that return a message
"""		 
class MessageSerializer(serializers.Serializer):
	status = serializers.CharField(default="ok")
	message = serializers.CharField()


"""
  For analytic models and concepts
"""		 
class ModelSerializer(serializers.Serializer):
	code = serializers.CharField()
	name = serializers.CharField()
	description = serializers.CharField()

	def to_representation(self, instance):
		# Here, 'instance' is an analytic mode
		
		return {"code": instance.code, "name": instance.name, 
			  "description": instance.description,
			  "concepts": get_concepts_level(instance, None)}
		 
class ConceptSerializer(serializers.Serializer):
	code = serializers.CharField()
	name = serializers.CharField()
	description = serializers.CharField()

	def to_representation(self, instance):
		# Here, 'instance' is an analytic mode
		
		return {"code": instance.code, "name": instance.name, 
			  "description": instance.description,
			  "children": get_concepts_level(instance.model, instance)}

#########################################
#
#	Serializers for annotations
#
#########################################
class ConceptStatsSerializer(serializers.Serializer):
	code = serializers.CharField()
	count = serializers.IntegerField()
	
class ModelStatsSerializer(serializers.Serializer):
	model = serializers.CharField(default="all")
	count = serializers.IntegerField()
	details = ConceptStatsSerializer(required=False, many=True)

class AnnotationStatsSerializer(serializers.Serializer):
	count = serializers.IntegerField()
	details = ModelStatsSerializer(many=True)
	#details = serializers.CharField(default="all")

class AnnotationSerializer(serializers.ModelSerializer):
	"""
		Serialization of annotations objects 
	"""
	class Meta:
		model = Annotation
		fields = ['ref']

	def to_representation(self, instance):
		# Here, 'instance' is an annotation	
		return annotation_to_rest(instance)
	
#########################################
#
#  Serializers for collection objects
#
#########################################

class CorpusSerializer(serializers.ModelSerializer):
	"""
		Serialization of Corpus objects 
	"""
	class Meta:
		model = Corpus
		fields = ['ref', 'title', 'short_title', 
				  'description', 'short_description',
				  'parent', 'composer', 'licence',
				  'copyright']
	
class OpusSerializer(serializers.ModelSerializer):
	"""
		Serialization of Opus objects 
	"""
	class Meta:
		model = Opus
		fields = ['ref', 'title', 'composer']

	def to_representation(self, instance):
		# Here, 'instance' is an Opus
		opusmeta = instance.to_serializable("abs_url")
		return opusmeta.to_json()
"""
   Ajouter: features, sources et files
		return {"ref": self.ref,
				"title": self.title,
				"composer": self.composer,
				"features": features,
				"sources": sources,
				"files": files
				}
"""	

class SourceSerializer(serializers.ModelSerializer):
	"""
		Serialization of source objects 
	"""
	class Meta:
		model = OpusSource
		fields = ['ref', 'source_type', 'url', 'description', 'source_file', 'manifest']

	def to_representation(self, instance):
		# Here, 'instance' is an Opus
		source_dict = instance.to_serializable("abs_url")
		return source_dict.to_json()

		 
class ArcIdxCorpusSerializer(serializers.Serializer):
	id = serializers.CharField(source="ref")
	name = serializers.CharField(source="title")
	description = serializers.CharField()
	public = serializers.BooleanField(default=True)
	types = serializers.ListField(
   		child=serializers.DictField(),
   		default=[{}]
   	) 
	rights = serializers.ListField(
   		child=serializers.CharField(),
   		default=["read"]
   	) 
	created = serializers.DateTimeField(source="creation_timestamp")

class ArkIdxImageSerializer(serializers.Serializer):
	"""
		ArkIndex API -- Serialization of IIIF images links
	"""
	
	url = serializers.CharField()
	width = serializers.CharField()
	height = serializers.CharField()

class ArkIdxElementSerializer(serializers.Serializer):
	"""
		ArkIndex API -- Serialization of Opus objects, aka elements in ArkIndex 
	"""
	def to_representation(self, instance):
		# Here, 'instance' is an Opus
		
		# An element that corresponds to an Opus is created without image
		metadata  = []
		metadata.append({"name": "opus_ref", "value": instance.ref})
		if instance.mei:
			metadata.append ({"name": "mei_url", "value": instance.mei.url}),

		return create_arkidx_element_dict(SCORE_TYPE,
										 instance.ref, 
										instance.title,
										  instance.corpus.ref, 
										  metadata, True, None)

class ArkIdxElementChildSerializer(serializers.Serializer):
	"""
		ArkIndex API -- Serialization of Opus objects, aka elements in ArkIndex 
	"""
	def to_representation(self, instance):
		# Here, 'instance' is an OpusSource of type IIIF
		# Not used, see views.py
		return []


class ArkIdxElementMetaDataSerializer(serializers.Serializer):
	"""
		ArkIndex API -- Serialization of IIIF images links
	"""
	
	key = serializers.CharField()
	value = serializers.CharField()

####
## Utility functions
####
	
def get_concepts_level(db_model, parent):
	"""Recursiveley find the children concepts of the parent parameter"""
	concepts = []
	db_concepts = AnalyticConcept.objects.filter(model=db_model, parent=parent)
	for concept in db_concepts:
		# Recursive call
		children = get_concepts_level(db_model, concept)
		concepts.append(
			{
				"code": concept.code,
				"name": concept.name,
				"description": concept.description,
				"display_options": concept.display_options,
				"icon": concept.icon,
				"children": children,
			}
		)
	return concepts


def annotation_to_rest(annotation):
	"""
	  Create the REST answer that describes an annotation
	"""

	if len(annotation.web_annotation) == 0:
		w3c = False # Change to true for a full W3C compliant
		webannot = annotation.produce_web_annotation()
		return webannot.get_json_obj(w3c)
	else:
		return annotation.web_annotation

def create_arkidx_element_dict(elt_type, id_element, name, corpus, metadata=[],
							has_children=False, zone=None):
	"""
	  Create a serializable dict compliant to the ArkIndex format
	"""
	return {"id" : id_element, "type": elt_type, 
					  "name" :name,
					  "corpus": corpus,
					  "thumbnail_url": "",
					  "metadata": [],
					  "classes": [],
					  "metadata": metadata,
					  "has_children": has_children,
					  "confidence": 1,
					  "zone": zone
					  }

