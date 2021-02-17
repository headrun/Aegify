# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from . import *
import codecs
import pandas as pd
from datetime import datetime
import csv, json, re, requests, os, time


def make_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

class MainPage(BasePage):
    def request(self):
        if self.key:
            url = 'https://data.cms.gov/%s/Opt-Out-Affidavits/7yuw-754z'%self.key
        else:
            url = self.url
        return Request(url)

    def parse(self, response):
        urls = 'https:'+''.join(re.findall('"contentUrl":"\w+...*', response.text)).split(',')[0].split(':')[-1]
        return NextPage(self, url=urls)

class NextPage(BasePage):
    def request(self):
        url = self.url.replace('"','')
        return Request(url)

    def parse(self, response):
        db_date = self.item_log.item.data_list.values()
        if db_date:
            from_db_last_date = db_date[0].get('json', {}).get('last_modified_at', '')
        else:
            from_db_last_date = ''
        last_mod = response.headers.get('Last-Modified', '').decode('utf-8')
        last_date = ''.join(re.findall('(.*) ',last_mod))
        today = datetime.now()
        folder_date_name = today.strftime('%Y%m%d')
        date_time = datetime.strptime(last_date, '%a, %d %b %Y %H:%M:%S').strftime('%Y-%m-%d')
        if (date_time and not from_db_last_date) or (str(date_time) > from_db_last_date):
            csv_processed_path = os.path.join(os.getcwd(), 'legal/output/cms_medicare/%s'%folder_date_name)
            make_dir(csv_processed_path)
            sel = Selector(text = response.text)
            timestr = time.strftime("%Y%m%d%H")
            input_text_file = 'CMS_OPTOUT_US'+'.csv'
            with open(csv_processed_path + '/' + input_text_file, 'wb') as f:
                f.write(sel.response.body)
            f.close()
            data = {'last_modified_at' : str(date_time)}
        else:
            data = {'last_modified_at': from_db_last_date}
        yield data

class CMSDetailSpider(BaseSpider):
    name = SOURCE + '_detail_terminal'
    source_name = SOURCE
    MODEL = 'DetailTerminal'
    main_page_class = MainPage
