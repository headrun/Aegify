from scrapy.http import Request

from .. import juicer

def URLS(num):
    return ['http://localhost:8000/static/admin/css/fonts.css?i=%s' % i for i in range(num)]

class SpiderMixin:
    source_name = 'test'

    @classmethod
    def create_data(self, response):
        return {'url': response.url, 'size': len(response.body)}

class TerminalSpider(SpiderMixin, juicer.TerminalSpider):
    def parse_main(self, response):
        yield self.create_data(response)
        self.got_page(response, response.url)

class StartUrlsSpider(TerminalSpider):
    name = 'juicer.start_urls'
    start_urls = URLS(3)

class StartRequestsSpider(TerminalSpider):
    name = 'juicer.start_requests'

    def start_requests_main(self):
        for url in URLS(2):
            yield Request(url)

class BrowseSpider(SpiderMixin, juicer.BrowseSpider):
    name = 'juicer.browse'
    start_urls = URLS(3)

    def parse_main(self, response):
        yield Request(response.url + '&next', callback=self.parse_done)

        return self.parse_done(response)

    def parse_done(self, response):
        yield self.get_page(response, 'test.item', response.url, response.url, data=self.create_data(response))

