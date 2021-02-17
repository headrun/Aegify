from scrapy.http import Request

from ..base import *

class MainPage(BasePage):
    def request(self):
        return Request('http://localhost:8000/static/admin/css/fonts.css?main=%s' % self.key)

    def parse(self, response):
        return NextPage(self)

class NextPage(BasePage):
    def request(self):
        return Request('http://localhost:8000/static/admin/css/fonts.css?next=%s' % self.key)

    def parse(self, response):
        data = BaseSchemaItem()

        key = self.key.split('_')[0]
        keys = [key] + [key+'_'+str(i) for i in range(4)]
        keys.remove(self.key)
        data.groups.append(
            SchemaItemGroup({
                'name': 'related',
                'keys': keys,
            })
        )
        return data

class TestSpider(BaseSpider):
    name = 'base'
    source_name = 'test'
    main_page_class = MainPage
