from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus, Upload
from workflow.Workflow import Workflow
import string
from django.core.files import File

import sys

import zipfile, os.path, io


class Command(BaseCommand):
	"""Import """

	help = 'Process a DMOS file, import MusicXML and MEI, create annotations'

	def add_arguments(self, parser):
		parser.add_argument('-o', dest='object_ref')
		parser.add_argument('-no_annotations', dest='no_annot')
		parser.add_argument('-no_score', dest='no_score')

	def handle(self, *args, **options):
			
		if options['object_ref'] is None:
			print ("You MUST provide the ref of the object (opus or corpus")
			exit(1)
			
		if options['no_annot'] is None:
			just_score = False
			print ("Annotations will be recomputed")
		else:
			# We only compute the score
			just_score = True
			print ("We only (re)compute the score")

		if options['no_score'] is None:
			just_annotations = False
			print ("The score will be recomputed")
		else:
			# We only compute annotations
			print ("We only (re)compute annotations")
			just_annotations = True
		
		try:
			opus = Opus.objects.get(ref=options['object_ref'])
			opus.parse_dmos(just_annotations, just_score)		 
		except Opus.DoesNotExist:
			print(f"Opus with ref {options['object_ref']} does not exist. Searching a corpus" )
			try:
				corpus = Corpus.objects.get(ref=options['object_ref'])
				corpus.parse_dmos(just_annotations, just_score)
			except Corpus.DoesNotExist:
				raise CommandError(f"No such object {options['object_ref']} " )
				exit(1)
