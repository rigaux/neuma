
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
import json
from jsonref import JsonRef


def tests(request):
	context = {"titre": "Tests Philippe"}

	# Root dir for sample data
	dmos_dir = os.path.join(settings.BASE_DIR, '../utilities/', 'dmos')
	# Where is the schema?
	schema_dir = os.path.join(dmos_dir, 'schema/')
	data_dir = os.path.join(dmos_dir, 'data/ex1/')
	
	# The main schema file
	schema_file = os.path.join(schema_dir, 'dmos_schema.json')
	# Where  json refs must be solved
	base_uri='file://' + schema_dir + '/'
	
	# Example to process
	input_file = "dmos_ex1.json"
	# Get the file name without extension
	input_file_root = os.path.splitext(os.path.basename(input_file))[0]

	# Parse the schema
	try:
		parser = CollabScoreParser(schema_file, base_uri)
		context['message_schema'] = "Le schéma est valide"
	except jsonschema.SchemaError as ex:
		context['message_schema'] = "Schema parsing error: " + str (ex)
	except Exception as ex:
		"Unexpected error during parser initialization: " + str (ex)

	
	# Load the data and resolve references
	#data = jsonref.load_uri('http://collabscore.org/dmos/data/dmos_data.json', 
	#					base_uri='http://collabscore.org/dmos/data/')
	
	data = jsonref.load_uri('file://' + data_dir + input_file, 
						base_uri='file://' + data_dir)

	# Write the full document in a local file
	#json_dir = os.path.join(settings.BASE_DIR, 'static', 'json')
	#with open(os.path.join(json_dir, 'full_example.json'), 'a') as the_file:
	#	json.dump(data, the_file)
	
	try:
		parser.validate_data (data)
		context['message'] = "Validation effectuée"
	except Exception as ex:
		context['message'] = str(ex)
	
	
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
	context["opus_url"] = "http://localhost:8000" + opus.musicxml.url
	
	context["annotations"] = score.annotations
	
	for dba in Annotation.objects.filter(opus=opus):
		dba.target.delete()
		dba.body.delete()
		dba.delete()
	for annotation in score.annotations:
		db_annot = Annotation.create_from_web_annotation(request.user, opus, annotation)
		db_annot.target.save()
		db_annot.body.save()
		db_annot.save()

	return render(request, 'collabscore/tests.html', context)

