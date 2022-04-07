
import os

from django.shortcuts import render
from manager.models import (
	Corpus,
	Opus
)
from django.conf import settings
from django.core.files.base import ContentFile

from lib.collabscore.parser import *

import jsonref
import json
from pprint import pprint
from jsonref import JsonRef


def tests(request):
	context = {"titre": "Tests Philippe"}

	# Root dir for sample data
	dmos_dir = os.path.join(settings.BASE_DIR, '../utilities/', 'dmos')
	# Where is the schema?
	schema_dir = os.path.join(dmos_dir, 'schema/')
	data_dir = os.path.join(dmos_dir, 'data/')
	
	# The main schema file
	schema_file = os.path.join(schema_dir, 'dmos_schema.json')
	# Where  json refs must be solved
	base_uri='file://' + schema_dir + '/'
	
	# Parse the schema
	try:
		parser = CollabScoreParser(schema_file, base_uri)
		context['message_schema'] = "Le schéma est valide"
	except jsonschema.SchemaError as ex:
		context['message_schema'] = "Schema parsing error: " + str (ex)
	except Exception as ex:
		"Unexpected error during parser initialization: " + str (ex)

	''' Load the schema
	schema  = json.load(sch_file)
	
	resolver = jsonschema.RefResolver(referrer=schema, 
									base_uri='file://' + data_dir + '/')

	try:
		# Check schema via class method call. Works, despite IDE complaining
		validator = jsonschema.Draft4Validator (schema, resolver=resolver)
		jsonschema.Draft4Validator.check_schema(schema)
		context['message_schema'] = "Le schéma est valide"
	except jsonschema.SchemaError as ex:
		context['message_schema'] = str (ex)
	'''
	
	# Load the data and resolve references
	#data = jsonref.load_uri('http://collabscore.org/dmos/data/dmos_data.json', 
	#					base_uri='http://collabscore.org/dmos/data/')
	
	data = jsonref.load_uri('file://' + data_dir + 'dmos_data.json', 
						base_uri='file://' + data_dir)

	# Write the full document in a local file
	with open(os.path.join(data_dir, 'full_example.json'), 'a') as the_file:
		json.dump(data, the_file)
		
	context["document"] = data
	
	try:
		parser.validate_data (data)
		context['message'] = "Validation effectuée"
	except Exception as ex:
		context['message'] = str(ex)
	
	# OK now build the internal score representation from the JSON content
	omr_score = OmrScore (data)
	
	context["omr_score"] = omr_score
	
	# Build the encoded score
	corpus = Corpus.objects.get(ref="all:potspourris")
	full_opus_ref = corpus.ref + settings.NEUMA_ID_SEPARATOR + "tst"
	try:
		opus = Opus.objects.get(ref=full_opus_ref)
	except Opus.DoesNotExist as e:
		# Create the Opus
		opus = Opus(corpus=corpus, ref=full_opus_ref, title="Test collabscore")
		opus.save()
		
	score = omr_score.get_score()
	score.write_as_musicxml ("/tmp/score.xml")
	with open("/tmp/score.xml") as f:
		score_xml = f.read()
	opus.musicxml.save("score.xml", ContentFile(score_xml))
	
	context["opus"] = opus
	context["opus_url"] = "http://localhost:8000" + opus.musicxml.url
	
	return render(request, 'collabscore/tests.html', context)

