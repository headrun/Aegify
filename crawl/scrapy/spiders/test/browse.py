from scrapy.http import Request, FormRequest

from ..browse import *

class MainPage(BasePage):
    def request(self):
        return Request('http://localhost:8000%s?1' % self.key)

    def parse(self, response):
        val = [
            self.spider.get_item(self, self.spider.ITEM_SOURCE_1, 'i1', ItemPage(self, parent_key=self.key)),
            self.spider.get_item(self, self.spider.ITEM_SOURCE_1, 'i2', OKSchemaItem()),
        ]

        val.append(OKSchemaItem()) # for browse item log.
        return val

class ItemPage(BasePage):
    def request(self):
        return Request('http://localhost:8000%s?next=%s' % (self.parent_key, self.key))

    def parse(self, response):
        return OKSchemaItem()

class TestSpider(BrowseSpider):
    name = 'browse'
    source_name = 'test'
    ITEM_SOURCE_1, _ = ('test.1', '')

    main_page_class = MainPage
