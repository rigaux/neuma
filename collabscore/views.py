
import os, datetime, math

from django.shortcuts import render
from manager.models import (
	Corpus,
	Opus
)
from django.conf import settings

import json
import jsonref
from pprint import pprint
from jsonref import JsonRef
import jsonschema 

def tests(request):
	context = {"titre": "Tests Philippe"}

	data_dir = os.path.join(settings.BASE_DIR, 'static', 'json')

	# Load the schema
	sch_file = open(os.path.join(data_dir, 'dmos_schema.json'))
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

	
	# Load the data
	#data_file = open()
	
	data = jsonref.load_uri('http://collabscore.org/dmos/data/dmos_data.json', base_uri='http://collabscore.org/dmos/data/')
	
	# Ecrivons le document complet dans un fichier
	with open(os.path.join(data_dir, 'full_example.json'), 'a') as the_file:
		json.dump(data, the_file)
		
	context["document"] = data
	
	try:
		jsonschema.validate (instance=data, schema=schema, resolver=resolver)
		context['message'] = "Validation effectuée"
	except jsonschema.ValidationError as ex:
		errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
		context['errors'] = errors
		context['message'] = "Erreur de validation données"
	except jsonschema.SchemaError as ex:
		context['message'] = str(ex)
		
	return render(request, 'collabscore/tests.html', context)

