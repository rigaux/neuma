from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus
from workflow.Workflow import Workflow
import string
from django.core.files import File

import sys

import zipfile, os.path, io
import json 

class Command(BaseCommand):
	"""Export a corpus as JSON LD documents"""

	help = 'Export a corpus as JSON LD documents'

	def add_arguments(self, parser):
		parser.add_argument('-f', dest='file_path', help="Path to the export directory")
		parser.add_argument('-c', dest='corpus_ref', help="Reference of the exported corpus")

	def handle(self, *args, **options):

		if options['file_path'] is None:
			print ("You MUST provide a path to an existing directory where JSON files will be written")
			exit(1)

		if options['corpus_ref'] is None:
			print ("You MUST provide the ref of an existing corpus")
			exit(1)

		try:
			corpus = Corpus.objects.get(ref=options['corpus_ref'])
			
			file_name = corpus.ref.replace (settings.NEUMA_ID_SEPARATOR, "-") + ".json"
			with open(os.path.join(options['file_path'], file_name),"w") as file:
				print (f"Writing file {file_name}")
				file.write (json.dumps(corpus.to_jsonld()))
		except Corpus.DoesNotExist:
			raise CommandError('Corpus with ref "%s" does not exist' % options['corpus_ref'])
			exit(1)
			

		print ("Done")
 
