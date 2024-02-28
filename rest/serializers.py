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
  Serializers for collection objects
"""
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
		lookup_field = "ref"

	def torepresentation(self, instance):
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

