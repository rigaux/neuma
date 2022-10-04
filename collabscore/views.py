
import os

from django.shortcuts import render
from manager.models import (
	Corpus,
	Opus,
	Annotation
)
from django.conf import settings
from django.core.files.base import ContentFile

from lib.collabscore.parser import CollabScoreParser, OmrScore

import jsonref
import jsonschema
import json


def index(request):
	context = {"titre": "CollabScore actions"}

	context["corpus"] = Corpus.objects.get(ref=settings.NEUMA_COLLABSCORE_CORPUS_REF)
	context["opus_list"] = []
	for opus in Opus.objects.filter(corpus=context["corpus"]):
		context["opus_list"].append({"opus_obj": opus,
									"url_mei" : request.build_absolute_uri(opus.mei.url),
									"url_annotations": 
									request.build_absolute_uri(
									"/rest/collections/collabscore:dmos_ex1/_annotations/region/_all/"),
									"label": opus.title})

	return render(request, 'collabscore/index.html', context)


def tests(request):
	context = {"titre": "Tests Philippe"}

	local_files = True
	
	if local_files:
		# Root dir for sample data
		# dmos_dir = os.path.join("file://" + settings.BASE_DIR, '../utilities/', 'dmos')
		dmos_dir = os.path.join("file://" + settings.BASE_DIR, 'static/', 'dmos')
	else:
		# Get from the collabscore server
		dmos_dir = 'http://collabscore.org/dmos/'
	
	# Where is the schema?
	schema_dir = os.path.join(dmos_dir, 'schema/')
	# The main schema file
	schema_file = os.path.join(schema_dir, 'dmos_schema.json')
	# Parse the schema
	try:
		parser = CollabScoreParser(schema_file, schema_dir)
		context['message_schema'] = "Le schéma est valide"
	except jsonschema.SchemaError as ex:
		context['message_schema'] = "Schema parsing error: " + ex.message
	except Exception as ex:
		context['message_schema'] = "Unexpected error during parser initialization: " + str (ex)
		return render(request, 'collabscore/tests.html', context)

	# Example to process
	input_file = "dmos_ex1.json"
	# Get the file name without extension
	input_file_root = os.path.splitext(os.path.basename(input_file))[0]

	# Load the data and resolve references	
	data_dir = os.path.join(dmos_dir, 'data/ex1/')
	file_url =  data_dir + input_file
	#print (f'Load {file_url} from {data_dir}')
	try:
		data = jsonref.load_uri(file_url,base_uri=data_dir)
	except Exception as ex:
		context['message'] = "Data loading error: " + str(ex)
		return render(request, 'collabscore/tests.html', context)

	#return render(request, 'collabscore/tests.html', context)

	# Write the full document in a local file
	#json_dir = os.path.join(settings.BASE_DIR, 'static', 'json')
	#with open(os.path.join(json_dir, 'full_example.json'), 'a') as the_file:
	#	json.dump(data, the_file)
	
	try:
		parser.validate_data (data)
		context['message'] = "Validation effectuée"
	except Exception as ex:
		context['message'] = "Validation error : " + str(ex)
	
	
	# Build the encoded score
	corpus = Corpus.objects.get(ref=settings.NEUMA_COLLABSCORE_CORPUS_REF)
	full_opus_ref = corpus.ref + settings.NEUMA_ID_SEPARATOR + input_file_root
	try:
		opus = Opus.objects.get(ref=full_opus_ref)
	except Opus.DoesNotExist as e:
		# Create the Opus
		opus = Opus(corpus=corpus, ref=full_opus_ref, title="Test collabscore")
		opus.save()
		
	# OK now build the internal score representation from the JSON content
	my_url = request.build_absolute_uri("/")[:-1] 
	omr_score = OmrScore (my_url + opus.get_url(), data)
	
	context["omr_score"] = omr_score
	score = omr_score.get_score()
	score.write_as_musicxml ("/tmp/score.xml")
	with open("/tmp/score.xml") as f:
		score_xml = f.read()
	opus.musicxml.save("score.xml", ContentFile(score_xml))
	
	score.write_as_mei ("/tmp/score.mei")
	with open("/tmp/score.mei") as f:
		score_mei = f.read()
	opus.mei.save("mei.xml", ContentFile(score_mei))

	context["opus"] = opus
	context["opus_url"] = my_url + opus.musicxml.url
	
	context["annotations"] = score.annotations
	
	# Now we know the full url of the MEI document
	score.uri = my_url + opus.mei.url

	for dba in Annotation.objects.filter(opus=opus):
		if dba.target is not None:
			dba.target.delete()
		if dba.body is not None:
			dba.body.delete()
		dba.delete()
	for annotation in score.annotations:
		annotation.target.resource.source = score.uri
		db_annot = Annotation.create_from_web_annotation(request.user, opus, annotation)
		db_annot.target.save()
		if db_annot.body is not None:
			db_annot.body.save()
		db_annot.save()

	return render(request, 'collabscore/tests.html', context)

