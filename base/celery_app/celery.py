from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from . import celeryconfig
from base.settings import DjangoUtil; DjangoUtil.init()
# set the default Django settings module for the 'celery' program.

app = Celery('tracking', include=['crawl.celery.tasks'])
app.config_from_object(celeryconfig)
# Load task modules from all registered Django app configs.
# app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))