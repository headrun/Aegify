from base.celery_app.celery import app

from .crawler_process_task import CrawlerProcessTask

app.register_task(CrawlerProcessTask())