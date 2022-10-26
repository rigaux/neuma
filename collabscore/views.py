
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
from numpy import True_


def index(request):
	context = {"titre": "CollabScore actions"}

	context["corpus"] = Corpus.objects.get(ref=settings.NEUMA_COLLABSCORE_CORPUS_REF)
	context["opus_list"] = []
	
	#for opus in Opus.objects.filter(corpus=context["corpus"]):
	for opus in Opus.objects.filter(ref__startswith=settings.NEUMA_COLLABSCORE_CORPUS_REF):
		if opus.mei:
			url_mei = request.build_absolute_uri(opus.mei.url)
		else:
			url_mei = ""
		url_dmos =""
		for source in opus.opussource_set.all():
			if source.ref == "dmos":
				url_dmos = request.build_absolute_uri(source.source_file.url)
		context["opus_list"].append({"opus_obj": opus,
									"url_mei" : url_mei, 
									"url_dmos": url_dmos,
									"url_annotations": 
									request.build_absolute_uri(
									"/rest/collections/collabscore:dmos_ex1/_annotations/region/_all/"),
									"label": opus.title})

	return render(request, 'collabscore/index.html', context)


def tests(request, opus_ref):
	context = {"titre": "Tests Philippe"}

	opus = Opus.objects.get(ref=opus_ref)
	url_dmos =""
	for source in opus.opussource_set.all():
		if source.ref == "dmos":
			url_dmos = request.build_absolute_uri(source.source_file.url)
	if url_dmos == "":
		context['message'] = "No DMOS file wih this Opus " 
		return render(request, 'collabscore/tests.html', context)


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

	try:
		data = jsonref.load_uri(url_dmos,base_uri="")
	except Exception as ex:
		context['message'] = "Data loading error: " + str(ex)
		return render(request, 'collabscore/tests.html', context)

	#return render(request, 'collabscore/tests.html', context)
	
	try:
		parser.validate_data (data)
		context['message'] = "Validation effectuée"
	except Exception as ex:
		context['message'] = "Validation error : " + str(ex)
	
		
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

