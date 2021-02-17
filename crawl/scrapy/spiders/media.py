from django.core import files

from .base import *

class MediaPage(BasePage):
    DEFAULT_FILE_NAME = 'media'

    def request(self):
        return Request(self.url, dont_filter=True)

    def parse(self, response):
        filepath = self.url.split('/')[-1] or self.DEFAULT_FILE_NAME

        return {'filepath': filepath, 'file': response.body}

class MediaSpider(BaseSpider):
    pass
