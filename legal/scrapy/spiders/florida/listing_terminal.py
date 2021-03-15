# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from . import *
import re
import csv
import codecs
import pandas as pd
import os
import time
from crawl.scrapy.spiders.base import *
from dateutil.parser import parse
from datetime import datetime

def make_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

class MainPage(BasePage):
    def request(self):
        if self.key:
            url = 'https://ww10.doh.state.fl.us/pub/ldo/data/' + self.key
        else:
            url = self.url
        headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'}
        return Request(url, headers=headers)

    def parse(self, response):
        data1 = self.item_log.item.data_list.values()
        if data1:
            from_db_last_date = data1[0].get('json', {}).get('last_modified_at', '')
        else:
            from_db_last_date = ''
        data = {}
        site_date = response.headers.get('Last-Modified', '').decode('utf-8')
        site_date_re = "".join(re.findall('(\d+ \D+ \d+ \d+:\d+:\d+)', site_date))
        site_date = parse(site_date_re)
        today = datetime.now()
        folder_date_name = today.strftime('%Y%m%d')
        if (site_date and not from_db_last_date) or str(site_date) > from_db_last_date:
            csv_processed_path = os.path.join(os.getcwd(), 'legal/output/%s/florida/'%folder_date_name)
            text_processing_path = os.path.join(os.getcwd(), 'legal/output/%s/florida/'%folder_date_name)
            make_dir(csv_processed_path)
            timestr = time.strftime("%Y%m%d")
            input_text_file = 'FL_MedicalLicensureBoard_US_STATE' +  '_' + (response.url).split('/')[-1]
            if 'txt' in response.url:
                sel = Selector(text = response.text)
                output_text_file = input_text_file.replace('txt', 'csv')
                with open(text_processing_path + input_text_file, 'wb') as f:
                    f.write(sel.response.body)
                df = pd.read_csv(text_processing_path + input_text_file, sep = "|", error_bad_lines=False, low_memory=False)
                df.to_csv(csv_processed_path + output_text_file, sep=";")
                f.close()
                if input_text_file:
                    try:
                        os.remove(text_processing_path + input_text_file)
                    except Exception as e:
                        print(e)
                        pass
                data = {'last_modified_at' : str(site_date)}
            elif 'pdf' in response.url:
                with open(text_processing_path + input_text_file, 'wb') as f:
                    f.write(response.body)
                    f.close()
        else:
            data = {'last_modified_at': from_db_last_date}
        yield data
class FloridaDetailSpider(BaseSpider):
    name = SOURCE + '_listing_terminal'
    source_name = SOURCE
    MODEL = 'ListingTerminal'
    main_page_class = MainPage
