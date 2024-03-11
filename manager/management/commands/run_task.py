from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from home.tasks import add, parse_dmos


class Command(BaseCommand):
	"""Import """

	help = 'Run an asynchronous task with Celery'

	def add_arguments(self, parser):
		parser.add_argument('-t', dest='task_name')

	def handle(self, *args, **options):
			
		if options['task_name'] is None:
			print ("You MUST provide the name of the task")
			exit(1)
		else:
			task_name = options['task_name']
			
		if task_name == "add":
			add.delay (1,1)
		
		if task_name=="parse_dmos":
			parse_dmos.delay("all:collabscore:saintsaens-ref:C006_0")
			
		"""send_email.delay(subject="New message", 
						message="The message", 
						recipients=["philippe.rigaux@cnam.fr"],
					)
		"""
		print ("Done")