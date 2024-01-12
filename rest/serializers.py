from rest_framework import serializers


# Types sent from the ArkIndex API
SCORE_TYPE = "Score"
PAGE_TYPE = "ScorePage"


"""
  Serializers for ArkIndex API
"""
class ArkIdxCorpusSerializer(serializers.Serializer):
	"""
		ArkIndex API -- Serialization of Corpus objects 
	"""
	
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

