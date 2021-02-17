# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from . import *
import codecs

class MainPage(BasePage):

    def request(self):
        if self.key:
            url = add_url(self.key)
        else:
            url = self.url
        return Request(url)

    def parse(self, response):
        sel = Selector(response)
        profile_link = "".join(sel.xpath(profile_data_xpath).extract())
        profile_url = add_url(profile_link)
        yield PageMeta(self, c_url=profile_url)

class PageMeta(BasePage):

    def request(self):
        return Request(self.c_url)

    def parse(self, response):
        links = response.xpath('//table[@align="center"]//tr//td[@valign="top"]/font/following-sibling::a//@href').extract()
        for i in links:
            key = i.split('/')[-1]
            yield self.spider.get_item(self, SOURCE, key, None, data={}, url=i)

class FloridaBrowseSpider(BrowseSpider):
    name = SOURCE + '_browse'
    source_name = SOURCE
    MODEL = 'Browse'
    main_page_class = MainPage
