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

	def handle(self, *args, **options):
			
		if options['object_ref'] is None:
			print ("You MUST provide the ref of the object (opus or corpus")
			exit(1)
		
		try:
			opus = Opus.objects.get(ref=options['object_ref'])
			opus.parse_dmos()						 
		except Opus.DoesNotExist:
			print(f"Opus with ref {options['object_ref']} does not exist. Searching a corpus" )
			try:
				corpus = Corpus.objects.get(ref=options['object_ref'])
				corpus.parse_dmos()
			except Corpus.DoesNotExist:
				raise CommandError(f"No such object {options['object_ref']} " )
				exit(1)
