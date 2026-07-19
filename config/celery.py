"""
Celery app for background jobs (store builds in apps.builder).
Broker not required until you run a worker.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("brandbox")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
