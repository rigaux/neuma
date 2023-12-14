from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Opus

from workflow.Workflow import Workflow

from lib.musicdiff import DetailLevel


class Command(BaseCommand):
	"""Import """

	help = 'Apply the MusicDiff algo. on two MEI scores'

	def add_arguments(self, parser):
		parser.add_argument('-o', dest='opus_ref')
		parser.add_argument('-d', dest='detail_level')
		parser.add_argument('-s', dest='show_pdf')

	def handle(self, *args, **options):
			
		if options['opus_ref'] is None:
			print ("You MUST provide the ref of the opus")
			exit(1)
		opus_ref = options['opus_ref']
		

		if options['detail_level'] is None:
			detail =  DetailLevel.GeneralNotesOnly
		else:
			detail = options['detail_level']

		if options['show_pdf'] is None:
			show_pdf = False
		else:
			show_pdf = True

		try:
			opus = Opus.objects.get(ref=opus_ref)
		except Opus.DoesNotExist:
			raise CommandError(f"Opus with ref '{opus_ref}' does not exist")
			exit(1)
		
		num_diffs = Workflow.compute_opus_diff(opus, detail, show_pdf)
		
		print (f"Done. Number of diffs = {num_diffs}")
