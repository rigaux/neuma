from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from workflow.Workflow import Workflow
import string
from django.core.files import File


import zipfile, os.path, io


class Command(BaseCommand):
    """Export the source files from the Elastic Search index"""

    help = 'Export the source files from the Elastic Search index'

    def add_arguments(self, parser):
        parser.add_argument('-o', dest='output_dir')

    def handle(self, *args, **options):
      Workflow.export_from_es (options['output_dir'])
