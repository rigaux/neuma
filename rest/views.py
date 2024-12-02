import hashlib
import urllib
import datetime
import jsonschema
import jsonref
import json
from jsonref import JsonRef

import os 
import zipfile

from django.core.files.base import ContentFile

from django.conf import settings
from django.db.models import Count, F

from rest_framework import viewsets
from . import serializers

from django.utils.dateformat import DateFormat

from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser, FileUploadParser, MultiPartParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import mixins
from rest_framework import generics

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from django.http import Http404

from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.reverse import reverse
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import permissions
from rest_framework.permissions import AllowAny
from rest_framework import renderers
from rest_framework.schemas import AutoSchema, ManualSchema

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from lxml import etree

# DMOS parser for validation
from lib.collabscore.parser import CollabScoreParser, OmrScore
from lib.collabscore.editions import Edition

# Asynchronous tasks
from home.tasks import parse_dmos

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

from .serializers import (
	LoginSerializer,
	MessageSerializer,
	ModelSerializer,
	ConceptSerializer,
	CorpusSerializer,
	OpusSerializer,
	SourceSerializer,
	EditionsSerializer,
	AnnotationStatsSerializer,
	AnnotationSerializer,
	ModelStatsSerializer,
	ArkIdxElementSerializer,
	ArkIdxElementChildSerializer,
	ArkIdxElementMetaDataSerializer,
	create_arkidx_element_dict
	)

# Music related functionalities
from music21 import converter, mei

import lib.music.Score as score_model
import lib.music.annotation as annot_mod
import lib.music.constants as constants_mod
import lib.music.opusmeta as opusmeta_mod
import lib.music.source as source_mod

from django.conf.global_settings import LOGGING

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import logging

# Get an instance of a logger

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
#
# Type for ressources
#
UNKNOWN_RESOURCE = "Unknown"
OPUS_RESOURCE = "Opus"
CORPUS_RESOURCE = "Corpus"
INTERNAL_REF_RESOURCE = "INTERNAL"  # For XML element inside an opus / MEI

'''
   Utility functions
'''

class JSONResponse(HttpResponse):
	"""
	An HttpResponse that renders its content into JSON.
	"""

	def __init__(self, data, **kwargs):
		content = JSONRenderer().render(data)
		kwargs["content_type"] = "application/json"
		super(JSONResponse, self).__init__(content, **kwargs)


'''
             Services implementation
'''

class CustomAuthToken(ObtainAuthToken):
	#serializer_class = LoginSerializer

	@extend_schema(operation_id="Login")
	def post(self, request):
		serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']
		token, created = Token.objects.get_or_create(user=user)
		return Response({
			'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })
		
@extend_schema(operation_id="NeumaApi_v3",
			 description="Welcome message to the Neuma REST API",
			 responses=MessageSerializer)
@api_view(["GET"])
@permission_classes((AllowAny, ))
def welcome(request):
	return JSONResponse({"message": "Welcome to Neuma web services root URL"})

@extend_schema(operation_id="CollectionsApi",
			 description="Welcome Neuma collections services",
			 responses=MessageSerializer)
@api_view(["GET"])
@permission_classes((AllowAny, ))
def welcome_collections(request):
	"""
	Welcome message to the collections services area
	"""
	mser = MessageSerializer({"message": "Welcome to Neuma web services on collections"})
	return JSONResponse(mser.data)


class ModelList(generics.ListAPIView):
	"""
	Get a of list of analytic models
	"""
	queryset = AnalyticModel.objects.all()
	serializer_class = ModelSerializer

	@extend_schema(operation_id="Modelist")
	def get(self, request):
		serializer = ModelSerializer(AnalyticModel.objects.all(), many=True)
		return Response(serializer.data)

@extend_schema(operation_id="ModelDetail")
class ModelDetail(generics.RetrieveAPIView):
	"""
	Get a of list of analytic models
	"""
	serializer_class = ModelSerializer
	queryset = AnalyticModel.objects.all()
	lookup_field="code"

@extend_schema(operation_id="ConceptDetail")
class ConceptDetail(generics.RetrieveAPIView):
	"""
	Get a of list of corpus given their parent
	"""
	serializer_class = ConceptSerializer
	queryset = AnalyticConcept.objects.all()

	def get(self, request, model_code, concept_code):
		try:
			# Take the concept and all its descendants
			concept =  AnalyticConcept.objects.get(model__code=model_code, code=concept_code)
			return JSONResponse(ConceptSerializer(concept).data)
		except AnalyticConcept.DoesNotExist:
			return JSONResponse(MessageSerializer(status="ko", message= f"Unknown concept: {concept_code}").data)
		
		"""
			#For latex encoding
			latex = "\\begin{tabular}{p{3cm}|p{2.5cm}|p{2.5cm}|p{2.5cm}|p{4cm}}\n"
			latex += "\\textbf{Concept (level 1)} & \\textbf{Concept (2)} & \\textbf{Concept (3)} & \\textbf{Concept (4)} & \\textbf{Description} \\\\ \\hline \n"
			latex += encode_concepts_in_latex(concepts, 0)
			latex += "\\hline \\end{tabular}\n"
			return HttpResponse(latex)
		"""

def encode_concepts_in_latex(concepts, level):
	latex = ""
	skip = ""
	inner_skip = ""
	for i in range(level):
		skip += " & "
	for i in range(4 - level):
		inner_skip += " & "

	for concept in concepts:
		latex += (
			skip + concept["name"] + inner_skip + concept["description"] + " \\\\ \n"
		)

		latex += encode_concepts_in_latex(concept["children"], level + 1)

	return latex



#############################
###
### Corpus services
###
############################


def get_object_from_neuma_ref(full_neuma_ref):
	"""
	Receives a path to a corpus or an Opus, check if it exists returns the object
	"""
	
	# We can receive the object request either as a path or as 
	# a local DB id. We use the latter if possible.
	
	if full_neuma_ref.isdigit ():
		try:
			return Opus.objects.get(id=int(full_neuma_ref)), OPUS_RESOURCE
		except Opus.DoesNotExist:
			# Unknown object
			return None, UNKNOWN_RESOURCE
	else:
		# OK, we check whether the path refers to an Opus of a corpus
		neuma_ref = full_neuma_ref.replace("/", settings.NEUMA_ID_SEPARATOR)

		try:
			return Opus.objects.get(ref=neuma_ref), OPUS_RESOURCE
		except Opus.DoesNotExist:
			# Not an opus. Maybe a corpus?
			try:
				return Corpus.objects.get(ref=neuma_ref), CORPUS_RESOURCE
			except Corpus.DoesNotExist:
				# Last possibility: an internal id in the MEI file of an Opus
				last_slash = full_neuma_ref.rfind("/")
				opus_id = full_neuma_ref[:last_slash].replace(
					"/", settings.NEUMA_ID_SEPARATOR
					)
				try:
					return Opus.objects.get(ref=opus_id), INTERNAL_REF_RESOURCE
				except Opus.DoesNotExist:
					# Unknown object
					return None, UNKNOWN_RESOURCE

@permission_classes((AllowAny, ))
class Element (APIView):
		
	@extend_schema(operation_id="Element",
		parameters=[
			OpenApiParameter(name='with_sources', 
							description='Include list of sources', 
							required=False, 
							type=str),
			]
		)
	
	def get(self, request, full_neuma_ref):
		"""
		Receive a path to a corpus or an Opus, returns the corpus or opus description
	
		The full_neuma_ref parameter is a path relative to the root corpus of the Neuma collections hierarchy. 
		Try for instance 'composers', then 'composers/couperin'. As a general rule, if the id
		of a corpus is c1:c2:cn, the reference to this corpus for REST services is c1/c2/cn.
	
		Note that you can obtain the list of corpuses by recursively calling the '_corpora'
		services for each corpus.
	
		To reference an opus , simply add the id of the opus to the corpus reference.
		"""

		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if object_type == UNKNOWN_RESOURCE:
			return Response(status=status.HTTP_404_NOT_FOUND)

		if request.method == "GET":
			if object_type == OPUS_RESOURCE:
				serializer = OpusSerializer(instance=neuma_object)
				return Response(serializer.data)
			elif object_type == CORPUS_RESOURCE:
				serializer = CorpusSerializer(instance=neuma_object)
				return Response(serializer.data)
			elif object_type == INTERNAL_REF_RESOURCE:
				opus = neuma_object
				last_slash = full_neuma_ref.rfind("/") + 1
				element_id = full_neuma_ref[last_slash:]

				# Check if element id matches a filename format
				filename, file_extension = os.path.splitext(element_id)
				if file_extension == ".xml":
					if filename == "mei" and opus.mei:
						meiString = ""
						with open(opus.mei.path, "r") as meifile:
							meiString = meifile.read()
						return HttpResponse(meiString, content_type="application/xml")
					else:
						return Response(status=status.HTTP_404_NOT_FOUND)
				else:
					print(
						"REST call for internal element request. Opus:"
						+ opus.ref
						+ " Element: "
						+ element_id
						)
					obj = {"id": element_id, "annotations": []}

					# Try to obtain the MEI document, which contains IDs
					if opus.mei:
						try:
							tree = etree.parse(opus.mei.path)
							xpath_expr = "//*[@xml:id='" + element_id + "']"
							# print ("Search for " + xpath_expr)
							element = tree.xpath(xpath_expr)
						except Exception as ex:
							logging.warning(
								"Error during parsing of file "
								+ opus.mei.path
								+ ": "
								+ str(ex)
								)
						db_annotations = Annotation.objects.filter(
							opus=opus, ref=element_id
							)
						for annotation in db_annotations:
							obj["annotations"].append(AnnotationSerializer(annotation).data)

					return JSONResponse(obj)

				return Response(status=status.HTTP_400_BAD_REQUEST)




@permission_classes((AllowAny, ))
class OpusFile (APIView):
	"""
	 Return the file  of a Opus, disabling caching
	 
	"""
	
	@extend_schema(operation_id="OpusFileGet")
	def get(self, request, full_neuma_ref):
		opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if opus.mei:
			with open(opus.mei.path, "r") as f:
				file_name = os.path.basename(opus.mei.path).split('/')[-1]
				content = f.read()
				resp = FileResponse(content) 
				resp['Content-type'] = "binary/octet-stream"  # source.source_type.mime_type
				resp["Content-Disposition"] = f"attachment; filename={file_name}"
				resp['Access-Control-Allow-Origin'] = '*'
				resp['Access-Control-Allow-Credentials'] = "true"
				resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
				resp['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Headers, Origin, Accept, ' \
                                               'X-Requested-With, Content-Type, Access-Control-Request-Method,' \
                                               ' Access-Control-Request-Headers, credentials'	
			return resp
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)


@extend_schema(operation_id="TopLevelCorpusList")
class TopLevelCorpusList(generics.ListAPIView):
	"""
	List top level corpora
	"""
	queryset = Corpus.objects.filter(
				parent__ref=settings.NEUMA_ROOT_CORPUS_REF
			)
	serializer_class = CorpusSerializer

@extend_schema(operation_id="CorpusList")
class CorpusList(generics.ListAPIView):
	"""
	Get a of list of corpus given their parent
	"""
	serializer_class = CorpusSerializer

	def get_queryset(self):
		parent_corpus = self.kwargs['full_neuma_ref']
		queryset = Corpus.objects.filter(parent__ref=parent_corpus)
		return queryset

@extend_schema(operation_id="OpusList")
class OpusList(generics.ListAPIView):
	"""
	Get a of list of opus given their corpus
	"""
	serializer_class = OpusSerializer

	def get_queryset(self):
		corpus_ref = self.kwargs['full_neuma_ref']
		queryset = Opus.objects.filter(corpus__ref=corpus_ref)
		return queryset

############
###
### Source services
###
############

@extend_schema(operation_id="SourceList")
class SourceList(generics.ListAPIView):

	serializer_class = SourceSerializer

	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		if opus_ref.isdigit():
			queryset = OpusSource.objects.filter(opus__id=int(opus_ref))
		else:
			queryset = OpusSource.objects.filter(opus__ref=opus_ref)
		return queryset
	
	@extend_schema(operation_id="SourceCreate")
	def put(self, request, full_neuma_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)

			source_type = SourceType.objects.get(code=request.data.get("source_type", ""))
			source_ref  = request.data.get("ref", "")
			description = request.data.get("description", "")
			source_url = request.data.get("url", "")
		except Opus.DoesNotExist:			
			serializer = MessageSerializer({"message": f"Opus {full_neuma_ref} does not exist "})
			return JSONResponse(serializer.data)
		except SourceType.DoesNotExist:			
			serializer = MessageSerializer({"message": "Source type " + request.data.get("source_type", "") + " does not exists"})
			return JSONResponse(serializer.data)		
		try:
			source = OpusSource.objects.get(opus=opus,ref=source_ref)
			serializer = MessageSerializer({"message": f"Source {source_ref}  already exists in opus {opus.ref}"})
			return JSONResponse(serializer.data)
		except OpusSource.DoesNotExist:
			db_source = OpusSource (opus=opus,ref=source_ref,source_type=source_type,
				description=description,url =source_url)
			db_source.save()
			serializer = MessageSerializer({"message": "Source created"})
			return JSONResponse("New source created")

class Source(APIView):
	serializer_class = SourceSerializer
	
	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		source_ref = self.kwargs['source_ref']
		opus, object_type = get_object_from_neuma_ref(opus_ref)
		return OpusSource.objects.filter(opus=opus, ref=source_ref)

	def get_object(self, full_neuma_ref, source_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			return OpusSource.objects.get(opus=opus, ref=source_ref)
		except OpusSource.DoesNotExist:
			raise Http404

	@extend_schema(operation_id="Source")
	def get(self, request, full_neuma_ref, source_ref, format=None):
		source = self.get_object(full_neuma_ref, source_ref)
		serializer = SourceSerializer(source)
		return JSONResponse(serializer.data)

	@extend_schema(operation_id="SourceUpdate")
	def post(self, request, full_neuma_ref, source_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			source_type = SourceType.objects.get(code=request.data.get("source_type", ""))
			description = request.data.get("description", "")
			source_url = request.data.get("url", "")
		except Opus.DoesNotExist:			
			serializer = MessageSerializer({"message": f"Opus {full_neuma_ref} does not exist "})
			return JSONResponse(serializer.data)
		except SourceType.DoesNotExist:
			serializer = MessageSerializer({"message": "Source type " + request.data.get("source_type", "") + " does not exists"})
			return JSONResponse(serializer.data)	
			
		try:
			source = OpusSource.objects.get(opus=opus,ref=source_ref)
			source.source_type = source_type
			source.description = description
			source.url = source_url
			source.save()
			serializer = MessageSerializer({"message": f"Source updated with description {source.description}"})
			return JSONResponse(serializer.data)	
		except OpusSource.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

	"""
	Too dangerous
	@extend_schema(operation_id="Source")
	def delete(self, request, full_neuma_ref, source_ref, format=None):
		source = self.get_object(full_neuma_ref, source_ref)
		serializer = SourceSerializer(source)
		return JSONResponse(serializer.data)
	"""

@extend_schema(operation_id="SourceManifest")
class SourceManifest(APIView):
	
	"""
	 Return the JSON manifest of a source
	 
	"""
	serializer_class = SourceSerializer
	
	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		source_ref = self.kwargs['source_ref']
		opus, object_type = get_object_from_neuma_ref(opus_ref)
		return OpusSource.objects.filter(opus=opus, ref=source_ref)

	def get_object(self, full_neuma_ref, source_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			return OpusSource.objects.get(opus=opus, ref=source_ref)
		except OpusSource.DoesNotExist:
			raise Http404

	def get(self, request, full_neuma_ref, source_ref, format=None):
		source = self.get_object(full_neuma_ref, source_ref)
		if source.manifest:
			with open(source.manifest.path, "r") as f1:
				return JSONResponse (json.loads(f1.read()))
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)

			#return JSONResponse({"status": "ko", "message": f"No manifest for  source {source_ref}"})

class SourceApplyEditions(APIView):
	
	"""
	 Apply a list of editions, sent in a JSON file, to a source. The
	 service returns the MusicXML file
	 
	"""
	serializer_class = SourceSerializer
	
	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		source_ref = self.kwargs['source_ref']
		opus, object_type = get_object_from_neuma_ref(opus_ref)
		return OpusSource.objects.filter(opus=opus, ref=source_ref)

	def get_object(self, full_neuma_ref, source_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			return OpusSource.objects.get(opus=opus, ref=source_ref)
		except OpusSource.DoesNotExist:
			raise Http404

	@extend_schema(operation_id="SourceApplyEditions")
	def post(self, request, full_neuma_ref, source_ref):
		source = self.get_object(full_neuma_ref, source_ref)
		tmp_src = source.apply_editions(request.data)
						
		if "format" in self.request.GET and self.request.GET["format"]=="json":
			json_answer = {"desc": f"Editions applied to source {source_ref} of opus {full_neuma_ref}",
						      "musicxml_path": tmp_src.source_file.url}
			return JSONResponse (json_answer)

		# We return the full XML file
		with open(tmp_src.source_file.path, "r") as f:
			content = f.read()
			resp = FileResponse(content) 
			resp['Content-type'] = "text/xml"  # source.source_type.mime_type
			#resp["Content-Disposition"] = f"attachment; filename={file_name}"
			resp['Access-Control-Allow-Origin'] = '*'
			resp['Access-Control-Allow-Credentials'] = "true"
			resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
			resp['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Headers, Origin, Accept, ' \
                                'X-Requested-With, Content-Type, Access-Control-Request-Method,' \
                              ' Access-Control-Request-Headers, credentials'	
			return resp

class SourceEditions(APIView):
	
	"""
	 Operations on editions
	"""
	serializer_class = EditionsSerializer
	#serializer_class = MessageSerializer
	
	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		source_ref = self.kwargs['source_ref']
		opus, object_type = get_object_from_neuma_ref(opus_ref)
		return OpusSource.objects.filter(opus=opus, ref=source_ref)

	def get_object(self, full_neuma_ref, source_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			return OpusSource.objects.get(opus=opus, ref=source_ref)
		except OpusSource.DoesNotExist:
			raise Http404

	@extend_schema(operation_id="SourceEditionsGet")
	def get(self, request, full_neuma_ref, source_ref):
		source = self.get_object(full_neuma_ref, source_ref)
		return JSONResponse (source.operations)

	@extend_schema(operation_id="SourceEditionsPut")
	def put(self, request, full_neuma_ref, source_ref):
		source = self.get_object(full_neuma_ref, source_ref)
		# In the case of PUT , we replace the editions
		source.operations = request.data
		source.save()
		serializer = MessageSerializer({"message": f"Editions replaced for source {source.ref} in opus {full_neuma_ref}"})
		return JSONResponse(serializer.data)	

	@extend_schema(operation_id="SourceEditionsPost")
	def post(self, request, full_neuma_ref, source_ref):
		#SourceEditions.serializer_class = MessageSerializer
		source = self.get_object(full_neuma_ref, source_ref)			
		json_editions = request.data
		# Check that the JSON does represent a valid edition
		for json_edition in json_editions:
			try:
				valid_ed = Edition.from_json(json_edition)
				source.add_edition(valid_ed)
			except Exception as ex:
				serializer = MessageSerializer({"status": "ko", "message": str(ex)})
				return JSONResponse(serializer.data)	
		
		source.save()
		serializer = MessageSerializer({"message": f"Editions updated for source {source.ref} in opus {full_neuma_ref}"})
		return JSONResponse(serializer.data)	

class SourceFile (APIView):
	"""
	 Return the file  of a source
	"""
	
	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		source_ref = self.kwargs['source_ref']
		opus, object_type = get_object_from_neuma_ref(opus_ref)
		return OpusSource.objects.filter(opus=opus, ref=source_ref)

	def get_object(self, full_neuma_ref, source_ref):
		try:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			return OpusSource.objects.get(opus=opus, ref=source_ref)
		except OpusSource.DoesNotExist:
			raise Http404

	@extend_schema(operation_id="SourceFileGet")
	def get(self, request, full_neuma_ref, source_ref):
		source = self.get_object(full_neuma_ref, source_ref)
		if source.source_file:
			with open(source.source_file.path, "r") as f:
				file_name = os.path.basename(source.source_file.path).split('/')[-1]
				content = f.read()
				resp = FileResponse(content) 
				resp['Content-type'] = "binary/octet-stream"  # source.source_type.mime_type
				resp["Content-Disposition"] = f"attachment; filename={file_name}"
				resp['Access-Control-Allow-Origin'] = '*'
				resp['Access-Control-Allow-Credentials'] = "true"
				resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
				resp['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Headers, Origin, Accept, ' \
                                               'X-Requested-With, Content-Type, Access-Control-Request-Method,' \
                                               ' Access-Control-Request-Headers, credentials'	
			return resp
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)


	@extend_schema(operation_id="SourceFilePost",	
				 responses= MessageSerializer)
	@parser_classes([MultiPartParser])
	def post(self, request, full_neuma_ref, source_ref):
		source = self.get_object(full_neuma_ref, source_ref)

		for filename, filecontent in request.FILES.items():
			name, extension = os.path.splitext(filename)
			print (f"Received file {filename} with extension {extension}")
			if extension == ".zip":
					zfile = zipfile.ZipFile(filecontent, 'r')
					for fname in zfile.namelist():
						base, extension = os.path.splitext (fname)
						if base == "" or base.startswith('_') or  base.startswith('.'):
							continue
						if extension == ".json":
							with zfile.open(fname) as myfile:
								fcontent = myfile.read().decode('utf-8')
								#print (fcontent)
								source.source_file.save(fname, ContentFile(fcontent))
							print (f"Found a file {fname} with extension {extension}")
			else:
				# We received directly a JSON file
				source.source_file.save(filename, filecontent)
		
		# Special case DMOS: parse the file and create XML files
		if source_ref==source_mod.OpusSource.IIIF_REF:
			opus, object_type = get_object_from_neuma_ref(full_neuma_ref)
			
			print ("Parsing DMOS in asynchronous mode")
			parse_dmos.delay(opus.ref)

		serializer = MessageSerializer({"message": "Source file uploaded"})
		return JSONResponse(serializer.data)	

############
###
### Annotation services
###
############

class AnnotationStats (APIView):
	"""
	 Returns statistics on the annotations of an Opus
	 
	"""
	serializer_class = AnnotationStatsSerializer	
	permission_classes = [AllowAny]
	
	@extend_schema(operation_id="AnnotationStats")
	def get(self, request, full_neuma_ref):
	
		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if type(neuma_object) is Opus:
			opus = neuma_object
		else:
			serializer = MessageSerializer(status="ko", 
										    message = f"Unknown opus {full_neuma_ref}")
			return JSONResponse(serializer.data)

		# Return stats of the annotations grouped by model
		total_annot = Annotation.objects.filter(opus=opus).count()
		model_count = Annotation.objects.filter(opus=opus).values(
		model_code=F('analytic_concept__model__code')).annotate(count= Count('*'))
		details = []	
		for mcount in model_count:
			details.append ({'model': mcount["model_code"],"count": mcount["count"]})
		serializer = AnnotationStatsSerializer({"model":"all",
											"count":total_annot,
											"details": details})
		return JSONResponse(serializer.data)

class AnnotationModelStats (APIView):
	"""
	 Returns statistics on the annotations of an Opus
	 
	"""
	serializer_class = ModelStatsSerializer	
	permission_classes = [AllowAny]
	
	@extend_schema(operation_id="AnnotationModelStats")
	def get(self, request, full_neuma_ref, model_code='_stats', concept_code="_stats"):
	
		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if type(neuma_object) is Opus:
			opus = neuma_object
		else:
			serializer = MessageSerializer(status="ko", 
										    message = f"Unknown opus {full_neuma_ref}")
			return JSONResponse(serializer.data)

		# The model is explicitly given
		try:
			db_model = AnalyticModel.objects.get(code=model_code)
			# Return stats of the model annotations grouped by concept
			total_annot = Annotation.objects.filter(opus=opus).count()
			concept_count = Annotation.objects.filter(opus=opus).filter(analytic_concept__model=db_model).values(
				concept_code=F('analytic_concept__code')).annotate(count= Count('*'))				
			details = []	
			for ccount in concept_count:
				details.append ({'code': ccount["concept_code"],"count": ccount["count"]})
			serializer = ModelStatsSerializer({"model": model_code,
											   "count":total_annot,
											  "details": details})
			return JSONResponse(serializer.data)
		except AnalyticModel.DoesNotExist:
			serializer = MessageSerializer({"status": "ko", 
									    "message" : f"Unknown analytic model: {model_code}"})
			return JSONResponse(serializer.data)

class AnnotationList(generics.ListAPIView):

	serializer_class = AnnotationSerializer

	def get_queryset(self):
		return Annotation.objects.all()
		
	@extend_schema(operation_id="AnnotationList")
	def get (self, request, full_neuma_ref, model_code='_stats', concept_code="_all"):

		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if type(neuma_object) is Opus:
			opus = neuma_object
		else:
			serializer = MessageSerializer({"status": "ko", 
								    "message": f"Unknown opus {full_neuma_ref}"})
			return JSONResponse(serializer.data)

		# The model is explicitly given
		try:
			db_model = AnalyticModel.objects.get(code=model_code)
		except AnalyticModel.DoesNotExist:
			serializer = MessageSerializer({"status": "ko", 
										    "message" : f"Unknown analytic model: {model_code}"})
			return JSONResponse(serializer.data)

		# Search for annotations
		if concept_code != "_all":
			try:
				db_annotations = Annotation.objects.filter(
					opus=opus, analytic_concept__code=concept_code
				)
			except AnalyticConcept.DoesNotExist:
				serializer = MessageSerializer({"status": "ko", 
										    "message" : f"Unknown concept {concept_code}"})
				return JSONResponse(serializer.data)
		else:
			db_annotations = Annotation.objects.filter(
				opus=opus, analytic_concept__model=db_model
			)
			
		annotations = {}
		for annotation in db_annotations:
			if not annotation.ref in annotations:
				annotations[annotation.ref] = []
			annotations[annotation.ref].append(AnnotationSerializer(annotation).data)

		return JSONResponse(annotations)

	@extend_schema(operation_id="AnnotationsClear")
	def delete(self, request, full_neuma_ref, model_code='_stats', concept_code="_all"):
		# The model is explicitly given
		try:
			db_model = AnalyticModel.objects.get(code=model_code)
		except AnalyticModel.DoesNotExist:
			serializer = MessageSerializer({"status": "ko", 
										    "message" : f"Unknown analytic model: {model_code}"})
			return JSONResponse(serializer.data)

		Annotation.objects.filter(
				opus__ref=full_neuma_ref, analytic_concept__model=db_model
			).delete()
		return JSONResponse({"message": f"All annotations of {full_neuma_ref} for annotation model {model_code} have been deleted"})

class AnnotationDetail(generics.RetrieveDestroyAPIView):
	serializer_class = AnnotationSerializer
	
	def get_queryset(self):
		return Annotation.objects.all()

	def get_object(self,  annotation_id):
		# Get the annotation 
		try:
			return Annotation.objects.get(id=annotation_id)
		except Annotation.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

	@extend_schema(operation_id="AnnotationDetail")
	def get(self, request, full_neuma_ref, annotation_id):
		try:
			db_annotation =  Annotation.objects.get(id=annotation_id)
			return JSONResponse(AnnotationSerializer(db_annotation).data)
		except Annotation.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

	@extend_schema(operation_id="AnnotationDelete")
	def delete(self, request, full_neuma_ref, annotation_id):
		try:
			db_annotation =  Annotation.objects.get(id=annotation_id)
			db_annotation.delete()
			serializer = MessageSerializer({"status": "ok", 
										    "message" : f"Successfully destroyed annotation {annotation_id}"})
			return JSONResponse(serializer.data)
		except Annotation.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

class AnnotationCreate(APIView):
	serializer_class = AnnotationSerializer
	
	def get_queryset(self):
		return Annotation.objects.all()

	@extend_schema(operation_id="AnnotationCreate")
	def put(self, request, full_neuma_ref):
		# Get the annotated object
		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if object_type == OPUS_RESOURCE:
			opus = neuma_object
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)

		# Instantiate a validator 
		try:
			# The main schema file
			schema_path = os.path.join (settings.BASE_DIR, "static", "json", "annotations", "schema")
			schema_file = 'file://' + os.path.join (schema_path, 'annotation_schema.json')
			# Where  json refs must be solved
			base_uri='file://' + schema_path + os.sep
			validator = CollabScoreParser(schema_file, base_uri)
		except jsonschema.SchemaError as ex:
			return JSONResponse({"error": "Schema parsing error: " + str (ex)})
		except Exception as ex:
			return JSONResponse({"error": "Unexpected error during schema parsing: " + str (ex)})

		# Parse the annotation
		data = JSONParser().parse(request) 
		logger.info ("Post data" + json.dumps(data))
		# Validate
		if not validator.validate_data (data):
			return JSONResponse({"errors": validator.error_messages})

		annotation = annot_mod.Annotation.create_from_json(data)
		concept_code = annotation.annotation_concept
		logger.info(
			f"Received a PUT request for annotation insertion. Concept: {annotation.annotation_concept}"
		)

		try:
			db_concept = AnalyticConcept.objects.get(code=concept_code)
		except AnalyticConcept.DoesNotExist:
			return JSONResponse({"error": f"Unknown concept code= {annotation.annotation_concept}"})
	
		db_annot = Annotation.create_from_web_annotation(request.user, opus, annotation)
		db_annot.target.save()
		if db_annot.body is not None:
			db_annot.body.save()
		db_annot.save()
		serializer = MessageSerializer({"status": "ok", 
						"message" : f"New annotation {db_annot.id} created on {opus.ref}", "annotation_id": db_annot.id}
								)
		return JSONResponse(serializer.data)

def annotation_to_rest(annotation):
	"""
	  Create the REST answer that describes an annotation
	"""

	webannot = annotation.produce_web_annotation()

	return webannot.get_json_obj()

#########################
#### MISC SERVICES
########################

@csrf_exempt
@api_view(["GET"])
def handle_user_request(request):
	"""
	  Return the currently connected user
	"""

	if request.method == "GET":
		if request.user:
			return JSONResponse(
				{
					"username": request.user.username,
					"full_name": request.user.get_username(),
				}
			)
		else:
			return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

########################################################
#
#  Revised API implementation, with classes and serializers
#
#########################################################

class RetrieveCorpus(APIView):
	
	serializer_class = CorpusSerializer
	
	@extend_schema(operation_id="RetrieveCorpus")
	def get(self, request, id):
		"""
			Returns a corpus description
		"""
		try:
			corpus = Corpus.objects.get(ref=id)
			serializer = CorpusSerializer(corpus)
			#serializer.is_valid(raise_exception=True)
			return JSONResponse(serializer.data)
		except Corpus.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

@extend_schema(operation_id="ListElements",
					  parameters=[
			OpenApiParameter(name='top_level', description='Filter by top_level', required=False, type=str),
			OpenApiParameter(name='with_has_children', description='Filter by children', required=False, type=str),
			OpenApiParameter(name='with_classes', description='Filter by classes', required=False, type=bool),
			]
		)

class ArkIdxListElements(generics.ListAPIView):
	
	serializer_class = ArkIdxElementSerializer
	def get_queryset(self):
		corpus_ref = self.kwargs['corpus']
		return Opus.objects.filter(corpus__ref=corpus_ref)

class ArkIdxListElementChildren(APIView):
	
	serializer_class = ArkIdxElementChildSerializer
	
	@extend_schema(operation_id="ListElementChildren",
		parameters=[
			OpenApiParameter(name='order', description='ordering of elements', required=False, type=str),
			OpenApiParameter(name='with_has_children', description='Filter by children', required=False, type=str),
			OpenApiParameter(name='with_classes', description='Filter by classes', required=False, type=bool),
			]
		)
	
	def get(self, request, id):
		try:
			opus = Opus.objects.get(ref = self.kwargs['id'])
			source = OpusSource.objects.get(opus=opus,ref=opusmeta_mod.OpusSource.IIIF_REF)
			# get an OpusSource object from the OpusMeta module
			my_url = request.build_absolute_uri("/")[:-1]
			source_dict = source.to_serializable(my_url)
			imgs = []
			i = 1
			for img in source_dict.images:
				zone = {"image": img.to_dict(),	"polygon": None}
				metadata = [{"name": "page", "value": i}]
				imgs.append( create_arkidx_element_dict(serializers.PAGE_TYPE, 
													opus.local_ref() + "-page" + str(i), 
											    opus.title + " - page " + str(i),
										  	    source.opus.ref, 
										  	    metadata,
										  	    False, zone))
				i = i+1
			return Response(imgs)
		except Opus.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		except OpusSource.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

class ArkIdxListElementMetaData(APIView):
	
	serializer_class = ArkIdxElementMetaDataSerializer
	
	@extend_schema(operation_id="ListElementMetaData",
		parameters=[
					OpenApiParameter(name='load_parents', description='Loading parents', required=False, type=str),
					]
		)
	
	def get(self, request, id):
		abs_url = request.build_absolute_uri("/")[:-1]
		try:
			opus = Opus.objects.get(ref = self.kwargs['id'])
			rval  = []
			rval.append({"name": "opus_ref", "value": opus.ref})
			if opus.mei:
				rval.append ({"name": "mei_url", "value": abs_url + opus.mei.url}),
			resp = Response (rval)
			return resp		
		except Opus.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		except OpusSource.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)


@permission_classes((AllowAny, ))
class ArkIdxGetElementFile (APIView):
	
	@extend_schema(operation_id="GetElementFile")
	def get(self, request, id):
		abs_url = request.build_absolute_uri("/")[:-1]
		try:
			opus = Opus.objects.get(ref = self.kwargs['id'])
			with open(opus.mei.path) as f:
				content = f.read()
			resp = FileResponse(content) # sendfile(request, opus.mei.path)
			resp['Content-type'] = 'application/xml'
			resp['Access-Control-Allow-Origin'] = '*'
			resp['Access-Control-Allow-Credentials'] = "true"
			resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
			resp['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Headers, Origin, Accept, ' \
                                               'X-Requested-With, Content-Type, Access-Control-Request-Method,' \
                                               ' Access-Control-Request-Headers, credentials'	
			return resp
		except Opus.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		except OpusSource.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
