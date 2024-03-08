import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scorelib.settings")

app = Celery("neuma")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Setup the Celery beat scheduler
"""
app.conf.beat_schedule = {
    "Every day at 5PM (UTC+0)": {
        "task": "neuma.users.tasks.send_daily_statistics",
        "schedule": crontab(hour=17, minute=0),
    },
}
"""
app.conf.timezone = settings.TIME_ZONE

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
