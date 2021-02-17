from scrapy.http import Request

from . import base, browse

class SpiderMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.crawl_type = 'catchup'

    def handle_data(self, page, obj):
        data = dict(obj)
        yield self.get_data(page, data)

class BrowseSpider(SpiderMixin, browse.BrowseSpider):
    def get_page(self, response, spider_name, url, sk, data=None, meta_data=None, section=''):
        return self.get_item(response.meta['page'], spider_name, sk, data, url=url)

class UrlPage(base.BasePage):
    def request(self):
        req = super().request()
        if req:
            return req

        item = self.item_log.item
        return Request(item.url, meta={'data': {'sk': item.key}})

class TerminalSpider(SpiderMixin, base.BaseSpider):
    main_page_class = UrlPage

    def get_page(self, response, spider_name, url, sk, data=None, meta_data=None, section=''):
        pass

    def got_page(self, response, sk, got_pageval=1):
        pass
