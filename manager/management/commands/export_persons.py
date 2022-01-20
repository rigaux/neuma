from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Person
import string
from django.core.files import File

from django.http import JsonResponse
import sys
import json
import zipfile, os.path, io


class Command(BaseCommand):
	"""Export the list of persons as a JSON file"""

	help = 'Export the list of persons as a JSON file'


	def handle(self, *args, **options):
		data = list(Person.objects.values())
		with open('static/persons/persons.json', 'w') as fp:
			json.dump(data, fp)
			
