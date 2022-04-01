
import os

from django.shortcuts import render
from manager.models import (
	Corpus,
	Opus
)
from django.conf import settings

from lib.collabscore.parser import *

import jsonref
import json
from pprint import pprint
from jsonref import JsonRef

def tests(request):
	context = {"titre": "Tests Philippe"}

	# Where is the schema?
	data_dir = os.path.join(settings.BASE_DIR, 'static', 'json')
	schema_file = os.path.join(data_dir, 'dmos_schema.json')
	base_uri='file://' + data_dir + '/'
	
	# Parse the schema
	try:
		parser = CollabScoreParser(schema_file, base_uri)
		context['message_schema'] = "Le schéma est valide"
	except jsonschema.SchemaError as ex:
		context['message_schema'] = "Schema parsing error: " + str (ex)
	except Exception:
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
	data = jsonref.load_uri('http://collabscore.org/dmos/data/dmos_data.json', 
						base_uri='http://collabscore.org/dmos/data/')
	
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
	
	return render(request, 'collabscore/tests.html', context)

