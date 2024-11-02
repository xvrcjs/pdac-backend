from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

#from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT", "redis://redis:6379")

app = Celery("settings", backend=REDIS_ENDPOINT, broker=REDIS_ENDPOINT)

app.conf.enable_utc = False
#app.conf.timezone = settings.CELERY_TIMEZONE
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
# celery beat


app.conf.beat_schedule = {
    "transcript_perfom_daily": {
        "task": "check_transcriptions_jobs_status",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}


""" @app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request)) """

# celery -A settings worker -l info --beat