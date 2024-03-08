
from celery import shared_task

from django.conf import settings
from django.core.mail import send_mail

@shared_task
def add(x, y):
	return x + y


@shared_task
def send_email(subject, message, recipients, html_message=None):
	send_mail(subject=subject,
			message=message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=recipients,
			fail_silently=False,
			html_message=html_message,
			)
