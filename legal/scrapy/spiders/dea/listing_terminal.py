from datetime import datetime
from scrapy.selector import Selector
from crawl.scrapy.spiders.base import DataPage
from . import *


def get_date(date):
    try:
        fmt_date = datetime.strptime(date, '%A, %B %d, %Y').date()
    except:
        try:
            fmt_date = datetime.strptime(date, '%B %d, %Y').date()
        except:
            fmt_date = ''
    return fmt_date

def add_url(link):
    url = 'https://www.deadiversion.usdoj.gov/'
    return urljoin(url, link)

class MainPage(BasePage):
    def request(self):
        url = self.url or add_url(self.key)
        return Request(url)

    def parse(self, response):
        sel = Selector(response)
        doctor_nodes = sel.xpath('//blockquote/p')
        file_year = response.url.split('/actions/')[-1].split('/index.html')[0]
        if not self.item_log.item.data_list.values():
            data_dict = {}
        else:
            data_dict = self.item_log.item.data_list.values()[0].get('json', {})
        for doctor_node in doctor_nodes:
            name = ''.join(doctor_node.xpath('./a/text()').extract())
            if not name: name = ''.join(doctor_node.xpath('./strong/a/text()').extract())
            detail_key = ''.join(doctor_node.xpath('./a/@href').extract())
            if not detail_key: detail_key = ''.join(doctor_node.xpath('./strong/a/@href').extract())
            unique_key = file_year + '/' + detail_key
            date = ''.join(doctor_node.xpath('./text()').extract_first()).strip('() ').replace('\xa0(', '')
            site_date = get_date(date)
            if detail_key:
                detail_url = '/'.join(response.url.split('/')[:-1])+ '/' + detail_key
                data = {'name': 'basic_details', 'basic_details': {'name': name, 'date': date, 'file_year': file_year}}
                if unique_key in data_dict.keys():
                    yield self.spider.get_item(self, SOURCE, unique_key, {}, url=detail_url, field_name='detail')
                    from_db_date = data_dict.get(unique_key, '')
                    if from_db_date:
                        db_date_checking = get_date(from_db_date)
                        if site_date > db_date_checking:
                            data_dict.update({unique_key: date})
                            yield self.spider.get_item(self, SOURCE, unique_key, data, url=detail_url, field_name='detail', last_scraped_at=datetime.today())
                else:
                    data_dict.update({unique_key: date})
                    yield self.spider.get_item(self, SOURCE, unique_key, data, url=detail_url, field_name='detail', last_scraped_at=datetime.today())
        yield data_dict

class MySpider(BrowseSpider):
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
