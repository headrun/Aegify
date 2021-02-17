# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from . import *
import codecs

class MainPage(BasePage):
    
    def request(self):
        if self.key:
            url = 'https://download.cms.gov/nppes/NPI_Files.html'
        else:
            url = self.url
        return Request(url)

    def parse(self, response):
        if 'html' in response.url:
            links = response.xpath('//a[contains(text(), "NPPES Data Dissemination")]//@href').extract()
            for link in links:
                url = domain_url + link.strip('.')
                yield self.spider.get_item(self, SOURCE, link.strip('.'), None, data={}, url=url)

class CmsnpaBrowseSpider(BrowseSpider):
    name = SOURCE + '_browse'
    source_name = SOURCE
    MODEL = 'Browse'
    main_page_class = MainPage
