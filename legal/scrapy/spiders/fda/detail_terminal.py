from scrapy.selector import Selector
from crawl.scrapy.spiders.base import BasePage, BaseSpider
from crawl.scrapy.validators import OKSchemaItem
from scrapy.http import Request
from . import *
from urllib.parse import urljoin
from datetime import datetime
import requests, csv, json, time, os, re
import pandas as pd

domain_url = "https://www.accessdata.fda.gov/scripts/SDA/"

def make_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

class MainPage(BasePage):

    def request(self):
        url = 'https://www.accessdata.fda.gov/scripts/SDA/sdNavigation.cfm?sd=%s&displayAll=true'%(self.key)
        return Request(url)

    def parse(self, response):
        last_updated_date = ''.join(response.xpath('//div[@id="pagetools_bottom"]/div[@id="pagetools_right"]/p[contains(text(), "Updated")]/text()').extract()).split(':')[-1].strip()
        site_updated_date = datetime.strptime(last_updated_date, "%m/%d/%Y").date()
        site_updated_date = site_updated_date.strftime("%Y-%m-%d")
        dwl_page_link = ''.join(response.xpath('//td[@align="left"]//span[@class="report"]/a[contains(text(), "link")]/@href').extract())
        if 'http' not in dwl_page_link:
            data_link = urljoin(domain_url, dwl_page_link)
            return NextPage(self, url=data_link, site_updated_date = site_updated_date)

class NextPage(BasePage):
    def request(self):
        url = self.url.replace('"','')
        return Request(url)

    def parse(self, response):
        db_modify_date = self.item_log.item.data_list.values()
        if db_modify_date:
            from_db_last_date = db_modify_date[0].get('json', {}).get('last_modified_at', '')
        else:
            from_db_last_date = ''
        site_updated_date = self.site_updated_date
        today = datetime.now()
        folder_date_name = today.strftime('%Y%m%d')
        if (site_updated_date and not from_db_last_date) or (str(site_updated_date) > from_db_last_date):
            csv_processed_path = os.path.join(os.getcwd(), "legal/output/fda/%s"%folder_date_name)
            excel_processing_path = os.path.join(os.getcwd(), "legal/output/fda/%s/"%folder_date_name)
            make_dir(csv_processed_path)
            #sel = Selector(text = response.body)
            timestr = time.strftime("%Y%m%d%H")
            dwl_output_text_file = 'FDADisqualifiedClinicalInvestigators_US_FDA'+ '.xls'
            output_text_file = dwl_output_text_file#.replace('xls', 'csv')
            with open(excel_processing_path + dwl_output_text_file, 'wb') as f:
                f.write(response.body)
            #df = pd.concat(pd.read_html(excel_processing_path + dwl_output_text_file))
            #df.to_csv(csv_processed_path + output_text_file, index = False)
            f.close()
            '''if dwl_output_text_file:
                try:
                    os.remove(excel_processing_path + dwl_output_text_file)
                except:
                    print(e)
                    pass'''

            data = {'last_modified_at': site_updated_date}
        else:
            data = {'last_modified_at': from_db_last_date}
        yield data

class ClinicalInvestigatorsTerminal(BaseSpider):
    name = SOURCE + '_terminal'
    source_name = SOURCE
    MODEL = 'DetailTerminal'
    main_page_class = MainPage

