import hashlib
import urllib

import subprocess

from xml.dom import minidom
from django.core.files.base import ContentFile

from django.conf import settings

from rest_framework import viewsets

from manager import models
from . import serializers

from django.utils.dateformat import DateFormat

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.decorators import api_view, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import *

from rest_framework import renderers
from rest_framework.schemas import AutoSchema, ManualSchema
from drf_yasg.utils import swagger_auto_schema
import coreapi

import json, os
import mido
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from lxml import etree

# Modèles
from manager.models import (
	Corpus,
	Opus,
	AnalyticModel,
	AnalyticConcept,
	Annotation,
	Upload,
)


# For transcription services
from transcription.models import QParse, Grammar, GrammarRule

from lib.workflow.Workflow import Workflow, workflow_import_zip
from quality.lib.NoteTree_v2 import MonophonicScoreTrees


from music21 import converter, mei
from lib.music.Score import *
from .forms import *
from django.conf.global_settings import LOGGING
from scorelib.analytic_concepts import *

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
#
# Type for ressources
#
UNKNOWN_RESOURCE = "Unknown"
OPUS_RESOURCE = "Opus"
CORPUS_RESOURCE = "Corpus"
INTERNAL_REF_RESOURCE = "INTERNAL"  # For XML element inside an opus / MEI


@csrf_exempt
@api_view(["GET"])
def welcome(request):
	"""
	Welcome message to the services area
	"""
	return JSONResponse({"Message": "Welcome to Neuma web services root URL"})

@csrf_exempt
@api_view(["GET"])
def welcome_collections(request):
	"""
	Welcome message to the collections services area
	"""
	return JSONResponse({"Message": "Welcome to Neuma web services on collections"})



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


@csrf_exempt
@api_view(["GET"])
def handle_neuma_ref_request(request, full_neuma_ref):
	"""
	Receives a path to a corpus or an Opus, returns the corpus or opsu description
	
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
			return JSONResponse(opus_to_rest(neuma_object))
		elif object_type == CORPUS_RESOURCE:
			return JSONResponse(corpus_to_rest(neuma_object))
		elif object_type == INTERNAL_REF_RESOURCE:
			opus = neuma_object
			last_slash = full_neuma_ref.rfind("/") + 1
			element_id = full_neuma_ref[last_slash:]

			# Check if element id matches a filename format
			filename, file_extension = os.path.splitext(element_id)
			print("Filename " + element_id + " = " + filename + file_extension)
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
					"REST call for note request. Opus:"
					+ opus.ref
					+ " Note: "
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
@swagger_auto_schema(methods=["get", "post"], auto_schema=None)
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


@csrf_exempt
@api_view(["GET"])
def handle_opus_concordance(request, opus_ref):
	"""
	Receives a JSON document encoding an event wrapped from the Web
	"""
	if request.method == "GET":
		try:
			opus = Opus.objects.get(ref=opus_ref)
		except Opus.DoesNotExist:
			return JSONResponse({"error": "Unknown opus"})


@csrf_exempt
@api_view(["POST"])
# Only admin user can import an upload
# @permission_classes((IsAdminUser, ))
def handle_import_request(request, full_neuma_ref, upload_id):
	"""
	  Request related to a corpus import file
	"""

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
			answer_list.append(opus_to_rest(opus))
		return JSONResponse(
			{"imported_file": upload.description, "imported_opera": answer_list}
		)


#############################
###
### Corpus services
###
############################


class TopLevelCorpusList(APIView):
	"""
	List top level corpora
	"""

	def get(self, request, format=None):
		"""
		  Return the list of top-level corpora
		"""

		try:
			tl_corpora = Corpus.objects.filter(
				parent__ref=settings.NEUMA_ROOT_CORPUS_REF
			)
		except Exception as ex:
			return JSONResponse({"error": str(ex)})

		corpora = []
		for child in tl_corpora:
			corpora.append(corpus_to_rest(child))

		return JSONResponse(corpora)


class CorpusList(APIView):
	"""
	List all corpus
	"""

	schema = ManualSchema(
		fields=[coreapi.Field("full_neuma_ref", required=True, description="tototo")]
	)

	def get(self, request, full_neuma_ref=settings.NEUMA_ROOT_CORPUS_REF, format=None):
		"""
		  Return the list of sub-corpus 
		"""

		neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
		if type(neuma_object) is Corpus:
			corpus = neuma_object
		else:
			return Response(status=status.HTTP_404_NOT_FOUND)

		try:
			children = Corpus.objects.filter(parent=corpus.id)
		except Exception as ex:
			return JSONResponse({"error": str(ex)})

		corpora = []
		for child in children:
			corpora.append(corpus_to_rest(child))

		return JSONResponse(corpora)


@csrf_exempt
@api_view(["GET"])
def handle_tl_corpora_request(request):
	"""
	  Return the list of top-level corpora
	"""

	if request.method == "GET":
		try:
			tl_corpora = Corpus.objects.filter(parent__ref=NEUMA_ROOT_CORPUS_REF)
		except Exception as ex:
			return JSONResponse({"error": str(ex)})

		corpora = []
		for child in tl_corpora:
			corpora.append(corpus_to_rest(child))

		return JSONResponse(corpora)


@csrf_exempt
@api_view(["GET"])
def handle_corpora_request(request, full_neuma_ref=settings.NEUMA_ROOT_CORPUS_REF):
	"""
	  Return the list of sub-corpus 
	"""

	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if type(neuma_object) is Corpus:
		corpus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "GET":
		try:
			children = Corpus.objects.filter(parent=corpus.id)
		except Exception as ex:
			return JSONResponse({"error": str(ex)})

		corpora = []
		for child in children:
			corpora.append(corpus_to_rest(child))

		return JSONResponse(corpora)


def corpus_to_rest(corpus):
	"""
	  Create the REST answer that describes a corpus
	"""

	answer = {
		"id": corpus.ref,
		"title": corpus.title,
		"shortTitle": corpus.short_title,
		"shortDescription": corpus.short_description,
	}
	if corpus.parent:
		answer["parent"] = corpus.parent.ref
	return answer


@csrf_exempt
@api_view(["GET"])
def handle_opera_request(request, full_neuma_ref):
	"""
	  Return the list of opera
	"""

	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if type(neuma_object) is Corpus:
		corpus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "GET":
		try:
			opera = Opus.objects.filter(corpus=corpus)
		except Exception as ex:
			return JSONResponse({"error": str(ex)})

		answer = []
		for opus in opera:
			answer.append(opus_to_rest(opus))

		return JSONResponse(answer)


############
###
### Opus services
###
############


@csrf_exempt
@api_view(["GET"])
def handle_files_request(request, full_neuma_ref):
	"""
	  Return an opus description and the list of files
	"""

	print("Handle files with " + full_neuma_ref)
	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if type(neuma_object) is Opus:
		opus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "GET":

		my_url = request.build_absolute_uri("/")[:-1]
		answer = opus_to_rest(opus)
		answer["files"] = {}
		for fname, fattr in Opus.FILE_NAMES.items():
			file = getattr(opus, fattr)
			if file:
				answer["files"][fname] = {"url": my_url + file.url}
		return JSONResponse(answer)


def opus_to_rest(opus):
	"""
	  Create the REST answer that describes an opus
	"""
	return opus.to_json()


############
###
### Annotation services
###
############


@csrf_exempt
@swagger_auto_schema(method="post", auto_schema=None)
@api_view(["POST"])
# Only authenticqted user cqn reauest q computqtion
# @permission_classes((IsAuthenticated(), ))
def compute_annotations(request, full_neuma_ref, model_code):
	"""
	Compute annotations for a model and an Opus
	"""

	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if type(neuma_object) is Opus:
		opus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "POST":
		print(
			"REST call for computing annotations. Opus: "
			+ opus.ref
			+ " Model: "
			+ model_code
		)

		try:
			db_model = AnalyticModel.objects.get(code=model_code)
		except AnalyticModel.DoesNotExist:
			print("error: Unknown analytic model: " + model_code)
			return JSONResponse({"error": "Unknown analytic model: " + model_code})

		# OK, compute
		if model_code == AMODEL_COUNTERPOINT:
			Workflow.cpt_opus_dissonances(opus)
		elif model_code == AMODEL_QUALITY:
			Workflow.quality_check(opus)
		else:
			print("error: Unknown analytic model: " + model_code)

		return JSONResponse({"ok": "Annotations computed"})


@csrf_exempt
@api_view(["GET"])
def handle_annotations_request(
	request, full_neuma_ref, model_code, concept_code="_all"
):
	"""
	Return a list of annotations for a given annotation model
	"""

	if request.method == "GET":

		print(
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

		# Search for annotations
		annotations = {}
		obj = {"annotations": annotations}

		try:
			db_model = AnalyticModel.objects.get(code=model_code)
		except AnalyticModel.DoesNotExist:
			return JSONResponse({"error": "Unknown analytic model"})

		if concept_code != "_all":
			try:
				# Take the concept and all its descendants
				db_concept = AnalyticConcept.objects.get(code=concept_code)
				concepts_list = db_concept.get_descendants(True)
				concept_name = db_concept.name
				db_annotations = Annotation.objects.filter(
					opus=opus, analytic_concept__in=concepts_list
				)
				print("Get  annotations for concept " + concept_code)
			except AnalyticConcept.DoesNotExist:
				return Response(status=status.HTTP_404_NOT_FOUND)
		else:
			print("Get  annotations for all concepts of model " + model_code)
			all_concepts = AnalyticConcept.objects.filter(model=db_model)
			db_annotations = Annotation.objects.filter(
				opus=opus, analytic_concept__in=all_concepts
			)

		for annotation in db_annotations:
			if not annotation.ref in annotations:
				annotations[annotation.ref] = []
			annotations[annotation.ref].append(annotation_to_rest(annotation))

		return JSONResponse(annotations)


@csrf_exempt
@swagger_auto_schema(methods=["post", "put"], auto_schema=None)
@api_view(["GET", "POST", "PUT"])
def handle_annotation_request(request, full_neuma_ref, annotation_id="-1"):
	"""
	  Actions on an annotation
	"""

	# Get the annotation if id supplied
	if annotation_id != "-1":
		new_annotation = False
		try:
			db_annotation = Annotation.objects.get(id=annotation_id)
		except Annotation.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
	else:
		new_annotation = True

	# Get the annotated object
	neuma_object, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if object_type == OPUS_RESOURCE:
		opus = neuma_object
	else:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "PUT":
		print("REST CALL to create a new annotation")
		concept_code = request.POST.get("concept", "")
		note_id = request.POST.get("note_id", "")
		comment = request.POST.get("comment", "")
		xml_fragment = request.POST.get("xml_fragment", "")
		logger.info(
			"Received a PUT request for annotation insertion. Concept:"
			+ concept_code
			+ " note id "
			+ note_id
			+ "Comment : "
			+ comment
			+ " XML fragment "
			+ xml_fragment
		)

		try:
			db_concept = AnalyticConcept.objects.get(code=concept_code)
		except AnalyticConcept.DoesNotExist:
			db_concept = AnalyticConcept.objects.get(code="composer")
			# return Response(status=status.HTTP_404_NOT_FOUND)

		user_annotation = Annotation(
			opus=opus,
			analytic_concept=db_concept,
			ref=note_id,
			offset="",
			fragment="",
			is_manual=True,
			comment=comment,
			xml_fragment=xml_fragment,
			user=request.user,
		)
		user_annotation.save()

		return JSONResponse("Create a new annotation")
	if request.method == "GET":
		return JSONResponse(annotation_to_rest(db_annotation))
	if request.method == "POST":
		concept_code = request.POST.get("concept", "")
		comment = request.POST.get("comment", "")

		logger.info(
			"Received a POST request for annotation update. Concept:"
			+ concept_code
			+ "Comment : "
			+ comment
		)
		try:
			db_concept = AnalyticConcept.objects.get(code=concept_code)
		except AnalyticConcept.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

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

@csrf_exempt
@swagger_auto_schema(method="post", auto_schema=None)
@api_view(["POST"])
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


# @csrf_exempt
# @api_view(['POST'])
# def compute_score_distance (request):
#	 """ Compute the distance and the list of differences between two MIDI
#		 The body must be a form-data with the fields:
#			 "score1" a score with one voice
#			 "score2" a score with one voice
#	 """
#	 if not "score1" in request.FILES and "score2" in request.FILES:
#		 return JSONResponse({"error": "No score1 and score present in the request"}, status=status.HTTP_400_BAD_REQUEST)

#	 #save localy the scores from the request
#	 scorefile1 = request.FILES["score1"]
#	 scorefile2 = request.FILES["score2"]
#	 tmp_score1_path= os.path.join(settings.TMP_DIR, 'tmp_score1.xml') #the path of the temporary midi files
#	 tmp_score2_path= os.path.join(settings.TMP_DIR, 'tmp_score2.xml')
#	 if os.path.exists(tmp_score1_path): # first delete them if they already exist
#		 os.remove(tmp_score1_path)
#	 if os.path.exists(tmp_score2_path): # first delete them if they already exist
#		 os.remove(tmp_score2_path)
#	 default_storage.save(tmp_score1_path, ContentFile(scorefile1.read())) #save it
#	 default_storage.save(tmp_score2_path, ContentFile(scorefile2.read()))

#	 #ora leggi il file con music21 e fai l'analisi
#	 score1 = converter.parse(tmp_score1_path)
#	 score2 = converter.parse(tmp_score2_path)

#	 #compute distance score and annotations
#	 try:
#		 cost, annotation_list = ComparisonProcessor.score_comparison(score1,score2)
#		 print(cost)
#		 print(annotation_list)
#		 return JSONResponse({"scores_distance": cost,
#							  "annotation_list" : annotation_list}, status=status.HTTP_200_OK)
#	 except Exception as e:
#		 print("Unable to retrieve the cost and annotations. Error: " + str(e))
#		 return JSONResponse({"error": "Unable to retreive the cost and comparison annotations"}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@swagger_auto_schema(method="post", auto_schema=None)
@api_view(["POST"])
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


####################
#
#		 TRANSCRIPTION API
#
###########################


@csrf_exempt
@api_view(["GET"])
def grammars(request):
	"""
	Return the list of grammars
	"""
	grammars = []
	for grammar in Grammar.objects.all():
		grammars.append(
			{
				"name": grammar.name,
				"meter_numerator": grammar.meter_numerator,
				"meter_denominator": grammar.meter_denominator,
			}
		)

	return JSONResponse(
		{"nb": len(grammars), "grammars": grammars}, status=status.HTTP_200_OK
	)


@csrf_exempt
@api_view(["GET", "POST", "PUT"])
def grammar(request, grammar_name):
	"""
	The name of a grammar
	"""

	if request.method == "GET":
		try:
			grammar = Grammar.objects.get(name=grammar_name)
			return JSONResponse(grammar.get_json(), status=status.HTTP_200_OK)
			# return JSONResponse({"Resultat ": "OK"}, status = status.HTTP_200_OK)
		except Grammar.DoesNotExist as e:
			return Response(
				"Grammar  " + grammar_name + " does not exist",
				status=status.HTTP_404_NOT_FOUND,
			)
	elif request.method == "PUT":
		# Check that the grammar does not exist
		try:
			grammar = Grammar.objects.get(name=grammar_name)
			return JSONResponse(
				{"error": 1, "message": "Grammar " + grammar_name + " already exists"},
				status=status.HTTP_400_BAD_REQUEST,
			)
		except Grammar.DoesNotExist as e:
			# Decode the input
			try:
				input_grammar = json.loads(request.body.decode())
				grammar = Grammar(
					name=grammar_name,
					ns=input_grammar["ns"],
					type_weight=input_grammar["type_weight"],
					meter_numerator=input_grammar["meter_numerator"],
					meter_denominator=input_grammar["meter_denominator"],
					initial_state=input_grammar["initial_state"],
				)
				grammar.save()
				for rule in input_grammar["rules"]:
					body = []
					occ = []
					for b in rule["body"]:
						body.append(b["state"])
						occ.append(b["occ"])
					gr_rule = GrammarRule(
						grammar=grammar,
						weight=rule["weight"],
						head=rule["head"],
						symbol=rule["symbol"],
						body=body,
						occurrences=occ,
					)
					gr_rule.save()

				return JSONResponse(
					{"error": 0, "message": "Grammar " + grammar_name + " created"},
					status=status.HTTP_200_OK,
				)
			except Exception as e:
				return JSONResponse(
					{"error": 1, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST
				)


@csrf_exempt
@api_view(["GET"])
def qparse(request):
	"""
	Run the QParse program
	"""
	try:
		jsonInput = json.loads(request.body.decode())

		# Find the grammar
		grammar_name = jsonInput["grammar"]
		input_name = jsonInput["name"]
		print(grammar_name)
		try:
			grammar = Grammar.objects.get(name=grammar_name)
		except Grammar.DoesNotExist:
			return JSONResponse({"error": 1, "message": "Grammar " + grammar_name 
									+ " does not exist"}, status=status.HTTP_200_OK)
		# Write the grammar in a TMP file
		grammar_file_name = os.path.join(settings.TMP_DIR, grammar_name + ".txt")
		with open(grammar_file_name, "w") as grammar_file:
			grammar_file.write(grammar.get_str_repr())
						
		#initialize the output json
		out_json = {
			'name':input_name,
			'grammar':grammar_name,
			'voices':[]
		}

		# iterate over voices
		for i, voice in enumerate(jsonInput["voices"]):
			print("Processing voice", i)
			input_file_name = os.path.join(settings.TMP_DIR, input_name + "_" + str(i) + ".txt")
			output_file_name = os.path.join(settings.TMP_DIR, input_name + "_" + str(i) + "-out.txt")
			with open(input_file_name, "w") as ifile:
				ifile.write(QParse.encodeInputVoiceAsText(voice))

			# OK ready for calling qparse. read the script, replace variables and execute
			with open(os.path.join(settings.SCRIPTS_ROOT, 'qparse.sh')) as script_file:
				script_file_content = script_file.read()
			# Get the script template by replacing the deployment-dependent paths
			sfile_content = script_file_content.replace ("{qparse_bin_dir}", settings.QPARSE_BIN_DIR
										 ).replace("{config_file_path}", settings.CONFIG_FILE_PATH
										 ).replace("{grammar_file}", grammar_file_name
										).replace("{input_file}", input_file_name
										).replace ("{output_file}", output_file_name)
			sfile_name = os.path.join(settings.TMP_DIR, "qparse_" + input_name  + "_" + str(i) + ".sh")
			with open(sfile_name, "w") as script_file:
				script_file.write(sfile_content)
			# Execute the script 
			subprocess.call(["chmod", "a+x", sfile_name])
			result = subprocess.call(sfile_name)

			# read the output file and extract the list of measures
			output_content = ""
			with open(output_file_name) as output_file:
				output_content  = output_file.read()
			# extract a list of trees for the current voice from the qparse string output
			voice_formatted_out = QParse.decodeOutput(output_content)
			# add the list in the out_json file for the current voice
			out_json['voices'].append(voice_formatted_out)


		return JSONResponse(out_json,status=status.HTTP_200_OK)
	except Exception as e:
		return JSONResponse({"message": "Exception raised while trying to un QParse. "+ str(e)}, 
							status=status.HTTP_400_BAD_REQUEST)


###################
# OTF TRANSCRIPTION
###################
@csrf_exempt
@api_view(["POST"])
def receive_midi_messages(request):
	data = json.loads(request.body)
	flags=[]
	keys=[]
	velocities=[]
	timestamps=[]
	#check if the body is correctly formatted
	try:
		for event in data:
			flags.append(event["flag"])
			keys.append(event["key"])
			velocities.append(event["velocity"])
			timestamps.append(event["timestamp"])
	except:
		JSONResponse({"error": "Incorrect midi message format"}, status=status.HTTP_400_BAD_REQUEST)
	
	return JSONResponse({"flag": flags, "key": keys, "velocity": velocities, "timestamp": timestamps}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(["GET"])
def test_midi_messages(request):
	return JSONResponse({"Response": "Working"}, status=status.HTTP_200_OK)
