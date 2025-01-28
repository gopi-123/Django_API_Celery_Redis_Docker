# schedule_tasks/celery.py
# Following lines helpful for compatibility between Python 2 and Python 3
from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schedule_tasks.settings")

# Broker URL: 'redis://redis:6379/0' specifies the Redis broker.
app = Celery("schedule_tasks", broker="redis://redis:6379/0")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
