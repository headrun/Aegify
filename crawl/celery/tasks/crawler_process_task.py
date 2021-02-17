import sys
import os
import requests
from base.utils import import_module_var, standalone_main
from celery import Task

from ..utility import Configure


class CrawlerProcessTask(Task):

    class InvalidArgumentsException(Exception):
        pass

    name = "crawler_process"

    def run(self, *args, **kwargs):
        try:
            config = Configure(kwargs.pop('site'))
            path = '.'.join(
                (os.environ.get('SCRAPY_PROJECT'), 'scrapy', 'process', 'ItemProcess'))
            ItemProcess = import_module_var(path, None)
            kwargs.setdefault('launch_scrapyd', False)
            kwargs.setdefault('celery_executor', True)
            standalone_main(ItemProcess, *args, **kwargs)
        except Exception as e:
            print(e)
            raise CrawlerProcessTask.InvalidArgumentsException(
                "Invalid Arguments passed..")
