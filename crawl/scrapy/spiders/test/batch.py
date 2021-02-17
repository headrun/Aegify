from scrapy.http import Request

from ..batch import *

class MainPage(BatchPage):
    def request(self):
        return Request('http://localhost:8000/tatic/admin/css/fonts.css?main=%s' % (','.join(self.keys)))

    def parse(self, response):
        for key in self.keys:
            self.add_data(key, OKSchemaItem())
        return self.get_data_list()
 
class TestSpider(BatchSpider):
    name = 'batch'
    source_name = 'batch'
    custom_settings  = {'BATCHSIZE': 2}
    main_page_class = MainPage
