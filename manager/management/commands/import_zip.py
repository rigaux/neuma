from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus, Upload
from workflow.Workflow import Workflow
import string
from django.core.files import File

import sys

import zipfile, os.path, io


class Command(BaseCommand):
	"""Import a zip file and applies the workflow to its content"""

	help = 'Import a zip file and applies the workflow to its content'

	def add_arguments(self, parser):
		parser.add_argument('-f', dest='file_path')
		parser.add_argument('-a', dest='async_mode')
		parser.add_argument('-c', dest='parent_corpus_ref')
		parser.add_argument('-r', dest='corpus_ref')
		parser.add_argument('-o', dest='import_options')

	def handle(self, *args, **options):
			
		if not (zipfile.is_zipfile(options["file_path"])):
			print ("Ce n'est pas un fichier ZIP")
			exit(1)
		else:
			zf = zipfile.ZipFile(options["file_path"], 'r')

		if options['corpus_ref'] is None:
			corpus_ref = "unknown_ref"
		else:
			corpus_ref = options['corpus_ref']

		if options['parent_corpus_ref'] is None:
			print ("You MUST provide the ref of the parent corpus")
			exit(1)
		
		import_options = []
		if options['import_options'] is not None:
			import_options.append(options['import_options'])
			
		if query_yes_no("Do you really want to import the zip archive %s in the parent corpus '%s'" % (options["file_path"],
						 options["parent_corpus_ref"]), 
		       			"no") == False:
				print ("Aborted")
				exit(1)

		try:
			parent_corpus = Corpus.objects.get(ref=options['parent_corpus_ref'])

			if "async_mode" in options and options["async_mode"] == "1":
				print ("Running in asynchronous mode")
				Workflow.async_import (upload, corpus_ref)
			else:
				print ("Running in synchronous mode")
				Workflow.import_zip(zf, parent_corpus, corpus_ref, import_options)						 
		except Corpus.DoesNotExist:
			raise CommandError('Corpus with ref "%s" does not exist' % options['parent_corpus_ref'])
			exit(1)
			

		print ("Import finished")
 
 
def query_yes_no(question, default="yes"):
	"""Ask a yes/no question via raw_input() and return their answer.

	"question" is a string that is presented to the user.
	"default" is the presumed answer if the user just hits <Enter>.
	It must be "yes" (the default), "no" or None (meaning
	an answer is required of the user).

	The "answer" return value is True for "yes" or False for "no".
	"""

	valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
	if default is None:
		prompt = " [y/n] "
	elif default == "yes":
		prompt = " [Y/n] "
	elif default == "no":
		prompt = " [y/N] "
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if default is not None and choice == "":
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")