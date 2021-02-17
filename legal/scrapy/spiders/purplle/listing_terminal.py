import json
from datetime import datetime
from crawl.scrapy.spiders.base import DataPage

from . import *

class MainPage(BasePage):
    def request(self):
        url = self.url
        return Request(url)

    def parse(self, response):
        mobile_num = response.xpath('//a[@style="text-decoration:none;"]/text()').extract()[-1].strip()
        loaction_add = ' '.join(response.xpath('//section[@id="location"]//span//text() | //section[@id="location"]//strong//a//text()').extract()).replace('\n','')
        timings = response.xpath('//div[@id="timming"]//p//text() | //p[@id="time"]//text()').extract()
        other_details = response.xpath('//div[contains(@class,"info-in mrt")]//p//span//text()').extract()
        meta_data = {
                     'mobileNumber':mobile_num,
                     'loactionAddress':loaction_add,
                     'timings':timings,
                     'otherDetails':other_details,
                     }
        return meta_data
        
class MySpider(BaseSpider):
    name = SOURCE + '_listing_terminal'
    source_name = SOURCE

    MODEL = 'ListingTerminal'
    main_page_class = MainPage

    def init_items(self):
        pass

    def get_item(self, page, source_name, key, obj, field_name=None, **kwargs):
        field = getattr(self.item_model, field_name).field
        save_item_log = self.create_item_log(field.related_model, key, source=self.get_item_source(source_name), **kwargs)
        setattr(page.item_log.item, field_name, save_item_log.item)

        kwargs.update({'key': key, 'item_log': save_item_log})
        if isinstance(obj, BasePage):
            obj.set_kwargs(kwargs)
            return obj
        else:
            return DataPage(page, obj, **kwargs)

