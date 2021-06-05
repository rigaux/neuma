from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Corpus, Opus, Upload
from workflow.Workflow import Workflow
import string
from django.core.files import File


import zipfile, os.path, io


class Command(BaseCommand):
    """Import a zip file and applies the workflow to its content"""

    help = 'Import a zip file and applies the workflow to its content'

    def add_arguments(self, parser):
        parser.add_argument('-u', dest='upload_id')
        parser.add_argument('-a', dest='async_mode')

    def handle(self, *args, **options):
        try:
            upload = Upload.objects.get(id=options['upload_id'])
        except Upload.DoesNotExist:
                raise CommandError('Upload file with id "%s" does not exist' % options['upload_id'])
                exit(1)
            
        if not (zipfile.is_zipfile(upload.zip_file.path)):
            print ("Ce n'est pas un fichier ZIP")

        if "async_mode" in options and options["async_mode"] == "1":
                print ("Running in asynchronous mode")
                Workflow.async_import (upload)
        else:
                print ("Running in synchronous mode")
                Workflow.import_zip(upload)                         
 