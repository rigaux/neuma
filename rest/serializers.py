from rest_framework import serializers

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

		return create_arkidx_element_dict("Opus", instance.ref, instance.title,
										  instance.corpus.ref, True, None)

class ArkIdxElementChildSerializer(serializers.Serializer):
	"""
		ArkIndex API -- Serialization of Opus objects, aka elements in ArkIndex 
	"""
	def to_representation(self, instance):
		# Here, 'instance' is an OpusSource of type IIIF
		
		# get an OpusSource object from the OpusMeta module
		source_dict = instance.to_serializable("")
		imgs = []
		for img in source_dict.images:
			zone = {"image": img.to_dict(),	"polygon": None}

			imgs.append( create_arkidx_element_dict("Opus", instance.ref, 
											instance.ref,
										  	instance.opus.ref, True, 
										  	zone))
		return imgs

####
## Utility functions
####
	
def create_arkidx_element_dict(elt_type, id_element, name, corpus, has_children, zone):
	"""
	  Create a serializable dict compliant to the ArkIndex format
	"""
	return {"id" : id_element, "type": elt_type, 
					  "name" :name,
					  "corpus": corpus,
					  "thumbnail_url": "",
					  "metadata": [{}],
					  "classes": [],
					  "has_children": has_children,
					  "confidence": 1,
					  "zone": zone
					  }
