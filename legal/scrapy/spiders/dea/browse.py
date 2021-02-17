from urllib.parse import urlparse

from . import *

def add_url(link):
    url = 'https://www.deadiversion.usdoj.gov/'
    return urljoin(url, link)

class MainPage(BasePage):
    def request(self):
        #self.name = self.item_log.item.name
        #self.area = ''
        #self.search_key = getattr(self, 'search_key', '')
        #url = 'https://www.deadiversion.usdoj.gov/crim_admin_actions/index.html' % quote(self.key)
        url = 'https://www.deadiversion.usdoj.gov/'
        url = urljoin(url, self.key)
        return Request(url)

    def parse(self, response):
        sel = Selector(response)
        university_links = sel.xpath('//blockquote/p/a/@href').extract()
        for key in university_links:
            url = add_url(key)
            yield self.spider.get_item(self, SOURCE, key, None, url=url)


class MySpider(BrowseSpider):
    name = SOURCE + '_browse'
    source_name = SOURCE

    MODEL = 'Browse'

    main_page_class = MainPage
