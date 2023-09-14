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
		parser.add_argument('-o', dest='opus_ref')

	def handle(self, *args, **options):
			
		if options['opus_ref'] is None:
			print ("You MUST provide the ref of the opus")
			exit(1)
		
		try:
			opus = Opus.objects.get(ref=options['opus_ref'])
			opus.parse_dmos()						 
		except Opus.DoesNotExist:
			raise CommandError('Opus with ref "%s" does not exist' % options['opus_ref'])
			exit(1)
			

		print ("Do not forget to index the new corpus (run scan_corpus with 'index' action)")
