from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from home.tasks import add, send_email

class Command(BaseCommand):
	"""Import """

	help = 'Run an asynchronous task with Celery'

	def add_arguments(self, parser):
		parser.add_argument('-t', dest='task_name')

	def handle(self, *args, **options):
			
		if options['task_name'] is None:
			print ("You MUST provide the name of the task")
			exit(1)
			
		add.delay (1,1)
		
		"""send_email.delay(subject="New message", 
						message="The message", 
						recipients=["philippe.rigaux@cnam.fr"],
					)
		"""
		print ("Done")