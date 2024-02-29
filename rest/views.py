import hashlib
import urllib
import datetime
import jsonschema
import jsonref
import json
from jsonref import JsonRef

import os 

from xml.dom import minidom
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

import mido
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from lxml import etree

# DMOS parser for validation
from lib.collabscore.parser import CollabScoreParser, OmrScore


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
	MessageSerializer,
	CorpusSerializer,
	OpusSerializer,
	SourceSerializer,
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


def get_object_from_neuma_ref(full_neuma_ref):
	"""
	Receives a path to a corpus or an Opus, check if it exists returns the object
	"""
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

'''
             Services implementation
'''

@extend_schema(operation_id="NeumaApi_v3",
			 description="Welcome message to the Neuma REST API",
			 responses=MessageSerializer)

@api_view(["GET"])
@permission_classes((AllowAny, ))
def welcome(request):
	return JSONResponse({"Message": "Welcome to Neuma web services root URL"})

@extend_schema(operation_id="CollectionsApi",
			 description="Welcome Neuma collections services",
			 responses=MessageSerializer)
@api_view(["GET"])
@permission_classes((AllowAny, ))
def welcome_collections(request):
	"""
	Welcome message to the collections services area
	"""
	return JSONResponse({"message": "Welcome to Neuma web services on collections"})


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
							obj["annotations"].append(annotation_to_rest(annotation))

					return JSONResponse(obj)

				return Response(status=status.HTTP_400_BAD_REQUEST)


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


@csrf_exempt
@api_view(["GET", "POST"])
def handle_concepts_request(request, model_code, concept_code="_all"):
	"""
	Interface with the analytic models and concepts
	"""

	if request.method == "GET":

		try:
			db_model = AnalyticModel.objects.get(code=model_code)
		except AnalyticModel.DoesNotExist:
			return JSONResponse({"error": "Unknown model: " + model_code})

		# Get the list of concepts of a given model
		print(
			"REST call for concept request. Model code: "
			+ model_code
			+ " Concept code "
		)
		if concept_code != "_all":
			try:
				# Take the concept and all its descendants
				db_concept = AnalyticConcept.objects.get(code=concept_code)
				concepts = get_concepts_level(db_model, db_concept)
			except AnalyticConcept.DoesNotExist:
				return Response(status=status.HTTP_404_NOT_FOUND)
		else:
			concepts = get_concepts_level(db_model, None)

		encoding = "json"  # See if we need another encoding later
		if encoding == "json":
			return JSONResponse(concepts)
		else:
			latex = "\\begin{tabular}{p{3cm}|p{2.5cm}|p{2.5cm}|p{2.5cm}|p{4cm}}\n"
			latex += "\\textbf{Concept (level 1)} & \\textbf{Concept (2)} & \\textbf{Concept (3)} & \\textbf{Concept (4)} & \\textbf{Description} \\\\ \\hline \n"
			latex += encode_concepts_in_latex(concepts, 0)
			latex += "\\hline \\end{tabular}\n"
			return HttpResponse(latex)

	elif request.method == "POST":
		obj = {"error": "Not yet implemented"}

		return JSONResponse(obj)


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


#Not used for the time being
def handle_import_request(request, full_neuma_ref, upload_id):

	#Request related to a corpus import file
	

	corpus, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if object_type != CORPUS_RESOURCE:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "POST":

		try:
			upload = Upload.objects.get(id=upload_id)
		except Upload.DoesNotExist:
			return JSONResponse({"error": "Unknown import file"})

		list_imported = Workflow.import_zip(upload)
		# task_id = async(workflow_import_zip, upload)

		answer_list = []
		if list_imported == None:
			return JSONResponse(
			{"error": "Empty list to import"})
		for opus in list_imported:
			answer_list.append(opus.to_json(request))
		return JSONResponse(
			{"imported_file": upload.description, "imported_opera": answer_list}
		)

#############################
###
### Corpus services
###
############################

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
		queryset = OpusSource.objects.filter(opus__ref=opus_ref, ref=source_ref)
		return queryset

	def get_object(self, full_neuma_ref, source_ref):
		try:
			return OpusSource.objects.get(opus__ref=full_neuma_ref, ref=source_ref)
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
		queryset = OpusSource.objects.filter(opus__ref=opus_ref, ref=source_ref)
		return queryset

	def get_object(self, full_neuma_ref, source_ref):
		try:
			return OpusSource.objects.get(opus__ref=full_neuma_ref, ref=source_ref)
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

class SourceFile (APIView):
	"""
	 Return the file  of a source
	 
	"""
	
	def get_queryset(self):
		opus_ref = self.kwargs['full_neuma_ref']
		source_ref = self.kwargs['source_ref']
		queryset = OpusSource.objects.filter(opus__ref=opus_ref, ref=source_ref)
		return queryset

	def get_object(self, full_neuma_ref, source_ref):
		try:
			return OpusSource.objects.get(opus__ref=full_neuma_ref, ref=source_ref)
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
		# Little trick for backward compatibility
		if source_ref == source_mod.OpusSource.DMOS_REF:
			source_ref = source_mod.OpusSource.IIIF_REF

		source = self.get_object(full_neuma_ref, source_ref)

		for filename, filecontent in request.FILES.items():
			source.source_file.save(filename, filecontent)
		
		# Special case DMOS: parse the file and create XML files
		if source_ref==source_mod.OpusSource.IIIF_REF:
			opus = Opus.objects.get(ref=full_neuma_ref)
			opus.parse_dmos()

		serializer = MessageSerializer({"message": "Source file uploaded"})
		return JSONResponse(serializer.data)	

############
###
### Annotation services
###
############


@csrf_exempt
@api_view(["GET"])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, ))
def handle_stats_annotations_request(
	request, full_neuma_ref, model_code='_stats', concept_code="_stats"
):
	"""
	Return a list of annotations for a given annotation model
	"""

	if request.method == "GET":

		logger.info(
			"REST call for annotations request. Opus:"
			+ full_neuma_ref
			+ " Model: "
			+ model_code
		)

		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if type(neuma_object) is Opus:
			opus = neuma_object
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)

		if not(model_code == "_stats"):
			# The model is explicitly given
			try:
				db_model = AnalyticModel.objects.get(code=model_code)
			except AnalyticModel.DoesNotExist:
				return JSONResponse({"error": f"Unknown analytic model: {model_code}"})

		if model_code=="_stats" and concept_code=="_stats":
			# Return stats of the annotations grouped by model
			total_annot = Annotation.objects.filter(opus=opus).count()
			model_count = Annotation.objects.filter(opus=opus).values(
						model_code=F('analytic_concept__model__code')).annotate(count= Count('*'))
			 				
			return JSONResponse({"total_annotations": total_annot, "count_per_model": model_count})
		elif concept_code=="_stats":
			# Return stats of the model annotations grouped by concept
			total_annot = Annotation.objects.filter(opus=opus).count()
			model_count = Annotation.objects.filter(opus=opus).filter(analytic_concept__model=db_model).values(
						concept_code=F('analytic_concept__code')).annotate(count= Count('*'))
			 				
			return JSONResponse({"annotation_model": db_model.code,
								   "total_annotations": total_annot, "count_per_concept": model_count})


@csrf_exempt
@api_view(["GET", "DELETE"])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, ))
def handle_annotations_request(
	request, full_neuma_ref, model_code, concept_code="_all"
):
	"""
	Return or DELETE a list of annotations for a given annotation model
	"""

	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if type(neuma_object) is Opus:
			opus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)
	# The model is explicitly given
	try:
		db_model = AnalyticModel.objects.get(code=model_code)
	except AnalyticModel.DoesNotExist:
		return JSONResponse({"error": f"Unknown analytic model: {model_code}"})

	if request.method == "GET":
		logger.info(
			f"REST call for reading all annotations of {opus.ref} in annotation model {db_model.code}"
		)

		# Search for annotations
		if concept_code != "_all":
			try:
				db_annotations = Annotation.objects.filter(
					opus=opus, analytic_concept__code=concept_code
				)
				logger.info("Get annotations for concept " + concept_code)
			except AnalyticConcept.DoesNotExist:
				return JSONResponse({"error": f"Unknown concept {concept_code}"})
		else:
			logger.info("Get  annotations for all concepts of model " + model_code)
			db_annotations = Annotation.objects.filter(
				opus=opus, analytic_concept__model=db_model
			)
			
		annotations = {}
		for annotation in db_annotations:
			if not annotation.ref in annotations:
				annotations[annotation.ref] = []
			annotations[annotation.ref].append(annotation_to_rest(annotation))

		return JSONResponse(annotations)
	if request.method == "DELETE":
		Annotation.objects.filter(
				opus=opus, analytic_concept__model=db_model
			).delete()

		logger.info(
			f"REST call for deleting all annotations of {opus.ref} in annotation model {model_code}"
		)
		return JSONResponse({"message": f"All annotations of {opus.ref} for annotation model {model_code} have been deleted"})

@csrf_exempt
@api_view(["GET", "POST", "DELETE"])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, ))
def handle_annotation_request(request, full_neuma_ref, annotation_id=-1):
	"""
	  Actions on an annotation 
	"""
	
	# Get the annotated object
	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if object_type == OPUS_RESOURCE:
		opus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	# Get the annotation 
	try:
		db_annotation = Annotation.objects.get(id=annotation_id)
	except Annotation.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "GET":
		return JSONResponse(annotation_to_rest(db_annotation))
	if request.method == "DELETE":
		db_annotation.delete()
		return JSONResponse({"message": f"Annotation {annotation_id} has been deleted for opus {opus.ref}"})


@csrf_exempt
@api_view(["PUT"])
@permission_classes((permissions.IsAuthenticatedOrReadOnly, ))
def put_annotation_request(request, full_neuma_ref):
	"""
	  Create a new annotation 
	"""
	
	# Get the annotated object
	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if object_type == OPUS_RESOURCE:
		opus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	# We need a user
	if not request.user.is_authenticated:
		return JSONResponse(
				"User is not authenticated. This call should not happen"
			)

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

	data = JSONParser().parse(request) 
	logger.info ("Post data" + json.dumps(data))

	if request.method == "PUT":
		logger.info ("REST CALL to create a new annotation")
		
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

		return JSONResponse({"message": f"New annotation created on {opus.ref}", "annotation_id": db_annot.id})

		return JSONResponse("Create a new annotation")

		if request.user.is_authenticated():
			if db_annotation.user.username == request.user.username:
				logger.info("Annotation made by the same  user")
				db_annotation.analytic_concept = db_concept
				db_annotation.comment = comment
				db_annotation.save()
				return JSONResponse(annotation_to_rest(db_annotation))
		else:
			# Do something for anonymous users.
			logger.warning("user is not authenticated")
			return JSONResponse(
				"User is not authenticated. This call should not happen"
			)

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


############
###
### Comparison services
###
############


## Save temporary the opus on the NEUMA database and return the reference
# INPUT: the URL of a score (MEI or MusicXML)
# return the reference of the saved opus


def save_external_opus(url_score):
	"""
	Save the score (MusicXML or MEI) linked in the URL to the neuma DB and return the reference
	:param url_score: the URL of the score
	:return: the reference of the score in the DB
	"""
	response = urllib.request.urlopen(url_score)
	data = response.read()
	# The score is stored in the external corpus
	external = Corpus.objects.get(ref=settings.NEUMA_EXTERNAL_CORPUS_REF)
	# The reference of the opus is a hash of the URL
	hash_object = hashlib.sha256(data).hexdigest()
	opus_ref = (
		settings.NEUMA_EXTERNAL_CORPUS_REF
		+ settings.NEUMA_ID_SEPARATOR
		+ hash_object[:16]
	)
	doc = minidom.parseString(data)
	root = doc.documentElement

	if root.nodeName == "mei":
		try:
			opus = Opus.objects.get(ref=opus_ref)
		except Opus.DoesNotExist as e:
			opus = Opus()
		opus.corpus = external
		opus.ref = opus_ref  # Temporary
		opus.mei.save("mei1.xml", ContentFile(data))
	else:
		# Hope this is a mMusicXML file
		opus = Opus.createFromMusicXML(external, opus_ref, data)
		# Produce the MEI file
		Workflow.produce_opus_mei(opus)
	opus.external_link = url_score
	opus.save()
	print("Opus created. Ref =" + opus.ref)
	return opus_ref


def compute_midi_distance(request):
	""" Compute the distance and the list of differences between two MIDI 
		The body must be a form-data with the fields: 
			"midi1" a monophonic .mid file with one track
			"midi2" a monophonic .mid file with one track
			"consider_offsets" a boolean string value ("True" or "False") saying if we consider also note offsets or only onsets
		return: the distance value and the list of differences to go from score1 to score2
				or an error 
	"""
	# check if the body is correctly formatted
	try:
		consider_offsets = request.data["consider_offsets"] == "True"
	except Exception as e:
		return JSONResponse(
			{
				"error": "consider_offsets (True or False) must be specified in the body "
			},
			status=status.HTTP_406_NOT_ACCEPTABLE,
		)

	if not "midi1" in request.FILES and "midi2" in request.FILES:
		return JSONResponse(
			{"error": "No midi1 and midi2 present in the request"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	midifile1 = request.FILES["midi1"]
	midifile2 = request.FILES["midi2"]
	tmp_midi1_path = os.path.join(
		settings.TMP_DIR, "tmp_midi1.mid"
	)  # the path of the temporary midi files
	tmp_midi2_path = os.path.join(settings.TMP_DIR, "tmp_midi2.mid")
	if os.path.exists(tmp_midi1_path):  # first delete them if they already exist
		os.remove(tmp_midi1_path)
	if os.path.exists(tmp_midi2_path):  # first delete them if they already exist
		os.remove(tmp_midi2_path)
	default_storage.save(tmp_midi1_path, ContentFile(midifile1.read()))  # save it
	default_storage.save(tmp_midi2_path, ContentFile(midifile2.read()))

	print(tmp_midi1_path)
	midi1 = mido.MidiFile(tmp_midi1_path)
	midi2 = mido.MidiFile(tmp_midi2_path)

	try:
		cost, annotation_list = ComparisonProcessor.midi_comparison(
			midi1, midi2, consider_rests=consider_offsets
		)
		return JSONResponse(
			{"comparison_midi": cost, "annotation_list": annotation_list},
			status=status.HTTP_200_OK,
		)
	except Exception as e:
		print("Unable to retrieve the cost and annotations. Error: " + str(e))
		return JSONResponse(
			{"error": "Unable to retreive the cost and comparison annotations"},
			status=status.HTTP_404_NOT_FOUND,
		)


def compute_score_distance(request):
	""" Compute the distance and the list of differences between two scores 
		The body must be a form-data with the fields: 
			"score1" a score with one voice
			"score2" a score with one voice
	"""
	if not "score1" in request.FILES and "score2" in request.FILES:
		return JSONResponse(
			{"error": "No score1 and score present in the request"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	# save localy the scores from the request
	scorefile1 = request.FILES["score1"]
	scorefile2 = request.FILES["score2"]
	tmp_score1_path = os.path.join(
		settings.TMP_DIR, "tmp_score1.xml"
	)  # the path of the temporary score
	tmp_score2_path = os.path.join(settings.TMP_DIR, "tmp_score2.xml")
	if os.path.exists(tmp_score1_path):  # first delete them if they already exist
		os.remove(tmp_score1_path)
	if os.path.exists(tmp_score2_path):  # first delete them if they already exist
		os.remove(tmp_score2_path)
	default_storage.save(tmp_score1_path, ContentFile(scorefile1.read()))  # save it
	default_storage.save(tmp_score2_path, ContentFile(scorefile2.read()))

	mei_path1 = Workflow.produce_temp_mei(tmp_score1_path, 1)["path_to_temp_mei"]
	mei_path2 = Workflow.produce_temp_mei(tmp_score2_path, 2)["path_to_temp_mei"]

	# now open the mei file with music21
	with open(mei_path1, "r") as f1:
		mei_string1 = f1.read()
	with open(mei_path2, "r") as f2:
		mei_string2 = f2.read()
	conv1 = mei.MeiToM21Converter(mei_string1)
	score1 = conv1.run()
	conv2 = mei.MeiToM21Converter(mei_string2)
	score2 = conv2.run()

	# compute distance score and annotations
	try:
		cost, annotation_list = ComparisonProcessor.score_comparison(score1, score2)
		print(cost)
		print(annotation_list)
		return JSONResponse(
			{
				"scores_distance": cost,
				"annotation_list": annotation_list,
				"score1": mei_string1,
				"score2": mei_string2,
			},
			status=status.HTTP_200_OK,
		)
	except Exception as e:
		print("Unable to retrieve the cost and annotations. Error: " + str(e))
		return JSONResponse(
			{"error": "Unable to retreive the cost and comparison annotations"},
			status=status.HTTP_404_NOT_FOUND,
		)
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
