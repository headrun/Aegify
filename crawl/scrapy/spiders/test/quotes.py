from scrapy.http import Request

from ..base import BasePage, BaseSpider
from ...utils import normalize

class PageMeta(BasePage):
    def request(self):
        return Request('http://quotes.toscrape.com/author/%s/'%self.key)

    def parse(self, response):
        author = normalize(''.join(response.xpath('//h3[@class="author-title"]/text()').extract()))
        born_on = normalize(''.join(response.xpath('//span[@class="author-born-location"]/text()').extract()))
        description = normalize(''.join(response.xpath('//div[@class="author-description"]/text()').extract()))
        return {"author":author,"born_on":born_on,"description":description}

class TestSpider(BaseSpider):
    name = "toscrape"
    main_page_class = PageMeta
