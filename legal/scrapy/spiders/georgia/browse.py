from . import *
from crawl.scrapy.spiders.base import DataPage
import math
from datetime import datetime
item_list = {}
class PaginationClass(BasePage):
    def request(self):
        current_page_no = 0
        valid_page = False
        current_page = ''.join(self.response.xpath('//table[@id="datagrid_results"]/tr')[-1].xpath('./td/font/span/text()').extract()).strip()
        current_page_no = int(current_page) - 1
        xpath_string = '//a/font[text()="%s"]/../@href'%(str(self.page))
        page_key = ''.join(self.response.xpath(xpath_string).extract()).strip()
        if page_key:
            self.page = self.page + 1
            valid_page = True
        else:
            if current_page_no == self.page - 2:
                page_list = self.response.xpath('//a/font[text()="..."]/../@href').extract()
                if page_list and (len(page_list) == 2 or current_page_no < 40):
                    page_key = page_list[-1]
                    self.page = self.page + 1
                    valid_page = True
                else:
                    page_key = ''
            else:
                LPN = math.floor(self.page/40)*40
                ACPN = math.floor(self.page/40)*40 - 40
                if int(current_page) >= ACPN and int(current_page)<= LPN:
                    if int(current_page) < LPN:
                        position = LPN-int(current_page)+1+(self.page%40)
                        position_key = self.response.xpath('//table[@id="datagrid_results"]/tr')[-1].xpath('./td/font/a/@href').extract()[-1]
                        page_key = position_key.replace(''.join(re.findall('doPostBack(.*),',position_key)).replace('(','').replace("'",'').split('_')[-1], 'ctl%d'%position)
                        self.page = self.page + 1
                        valid_page = True
                else:
                    page_key = self.response.xpath('//table[@id="datagrid_results"]/tr')[-1].xpath('./td/font/a/@href').extract()[0]
                current_page_no = LPN
        data = {
                "__EVENTTARGET": ''.join(re.findall('doPostBack(.*),',page_key)).replace('(','').replace("'",''),
                "__EVENTARGUMENT": '',
                "__VIEWSTATE": ''.join(self.response.xpath('//input[@id="__VIEWSTATE"]/@value').extract()).strip(),
                "__VIEWSTATEGENERATOR": ''.join(self.response.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()).strip(),
                "__EVENTVALIDATION": ''.join(self.response.xpath('//input[@id="__EVENTVALIDATION"]/@value').extract()).strip()
        }
        if current_page_no:
            data["CurrentPageIndex"] = str(current_page_no)
        return FormRequest('https://gcmb.mylicense.com/verification/SearchResults.aspx', formdata=data, meta = {'validPage':valid_page, 'cookiejar': self.cookiejar}, dont_filter=True)

    def parse(self, response):
        result_rows = response.xpath('//table[@id="datagrid_results"]/tr')
        if response.status in [302, 404] or not result_rows:
            keys = ['licenseType', 'status', 'licenseNumber', 'address']
            for each_row in item_list.get(self.key, []):
                data = {}
                person_name = ''.join(each_row.xpath('./td/table/tr/td/a/text()').extract()).strip()
                if person_name:
                    data['personName'] = personNameFormat(person_name)
                else:
                    data['personName'] = None
                td_data = each_row.xpath('./td/span/text()').extract()
                for (key, value) in zip(keys, td_data):
                    data[key] = value.strip()
                unique_key = generate_unique_key([data.get('licenseType', ''), data.get('licenseNumber', ''), data.get('status', ''), person_name, data.get('address', '')])
                yield self.spider.get_item(self, SOURCE, unique_key, data, field_name='detail', last_scraped_at=datetime.today())
            if response.status in [302, 404]:
                yield {'pageNumber':self.page - 1}
                raise Exception("Session has expired.")
            elif not result_rows:
                self.kwargs['active'] = False
                yield {'pageNumber':1, 'totalPages':self.page - 1}
                return OKSchemaItem()
        if response.meta['validPage'] and result_rows:
            if item_list.get(self.key, []):
                item_list.get(self.key).extend(result_rows[1:-1])
            else:
                item_list[self.key] = result_rows[1:-1]
        if result_rows:
            yield PaginationClass(self, response=response, page = self.page, cookiejar=response.meta.get("cookiejar"))

class MainPage(BasePage):
    next_class = PaginationClass
    page_type = 'browsePage'
    def request(self):
        return Request('https://gcmb.mylicense.com/verification/', dont_filter=True, meta={'cookiejar': self.key})
    
    def parse(self, response):
        request_data = {}
        site_key = ''.join(response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').extract()).strip()
        request_data["__EVENTTARGET"] = ''
        request_data["__EVENTVALIDATION"] = ''.join(response.xpath('//input[@id="__EVENTVALIDATION"]/@value').extract()).strip()
        request_data["__VIEWSTATE"] = ''.join(response.xpath('//input[@id="__VIEWSTATE"]/@value').extract()).strip()
        request_data["__VIEWSTATEGENERATOR"] = ''.join(response.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value').extract()).strip()
        count = 5
        request_data["g-recaptcha-response"] = ''
        while count >= 0:
            request_data["g-recaptcha-response"] = get_googlecaptcha('https://gcmb.mylicense.com/verification/', site_key)
            if request_data["g-recaptcha-response"]:
                break
            count = count - 1
        if not request_data["g-recaptcha-response"]:
            raise Exception("Deapth By Captcha doesn't responded.") 
        if self.page_type == 'terminalPage':
            request_data.update(data_from_unique_key(self.key))
        else:
            request_data['licenseType'] = ' '.join(self.key.split('-'))
        return searchPage(self, request_data = request_data, next_class=self.next_class, page_type=self.page_type, cookiejar=response.meta.get("cookiejar"))

class searchPage(BasePage):
    def request(self):
        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE':self.request_data.get('__VIEWSTATE','') ,
            '__VIEWSTATEGENERATOR':self.request_data.get('__VIEWSTATEGENERATOR',''),
            '__EVENTVALIDATION':self.request_data.get('__EVENTVALIDATION','') ,
            't_web_lookup__first_name': '',
            't_web_lookup__license_type_name': self.request_data.get('licenseType', ''),
            't_web_lookup__last_name': '',
            't_web_lookup__license_status_name': self.request_data.get('status', ''),
            't_web_lookup__license_no': self.request_data.get('licenseNumber', ''),
            't_web_lookup__addr_city': '',
            't_web_lookup__addr_state': '',
            'g-recaptcha-response': self.request_data.get('g-recaptcha-response',''),
            'sch_button': 'Search'
        }
        return FormRequest('https://gcmb.mylicense.com/verification/', formdata=data, dont_filter=True, meta={'cookiejar': self.cookiejar})
    def parse(self, response):
        return resultPage(self,response=response, next_class=self.next_class, page_type=self.page_type, cookiejar=response.meta.get("cookiejar"))

class resultPage(BasePage):
    def request(self):
        return Request('https://gcmb.mylicense.com/verification/SearchResults.aspx',dont_filter=True, meta={'cookiejar': self.cookiejar})
    def parse(self, response):
        if response.status in [302, 404]:
            raise Exception("Session has expired.")
        if self.page_type == "browsePage":
            db_data = self.item_log.item.data_list.values()
            if db_data:
                page_no = db_data[0].get('json', {}).get('pageNumber', '')
            else:
                page_no = 1
            result_rows = response.xpath('//table[@id="datagrid_results"]/tr')
            if page_no == 1 and result_rows:
                if item_list.get(self.key, []):
                    item_list.get(self.key).extend(result_rows[1:-1])
                else:
                    item_list[self.key] = result_rows[1:-1]
                page_no = page_no + 1
            if result_rows:
                yield PaginationClass(self,response=response, page = page_no, cookiejar=response.meta.get("cookiejar"))
        else:
            yield self.next_class(self, response = response, cookiejar=response.meta.get("cookiejar"))

class GeorgiaBrowseSpider(BrowseSpider):
    name = SOURCE + '_listing_terminal'
    source_name = SOURCE
    custom_settings = {"COOKIES_ENABLED":True}
    handle_httpstatus_list = [302, 404]
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


