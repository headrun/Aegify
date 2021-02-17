# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from . import *
import csv, os, re
import pandas as pd
import os, re
import time, shutil
import requests, zipfile, io
from zipfile import ZipFile
from datetime import datetime


def make_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


class MainPage(BasePage):
    def request(self):
        if self.key:
            url = domain_url + self.key
        else:
            url = self.url
        headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'}
        return Request(url, headers=headers)

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
            z = zipfile.ZipFile(io.BytesIO(response.body))
            zip_file = os.path.join(os.getcwd(), 'legal/output/cms_npi/%s/zipfiles/'%folder_date_name)
            files = z.extractall(zip_file)
            pth=os.path.join(os.getcwd(), zip_file)
            for item in os.listdir(path=pth):
                if 'npidata_pfile_' in item and '.csv' in item and not 'Header.csv' in item or '.xlsx' in item:
                    zip_ = os.path.join(os.getcwd(), 'legal/output/cms_npi/%s/zipfiles/'%folder_date_name)
                    make_dir(zip_)
                    zip_ = zip_ + item
                    csv_processed_path = os.path.join(os.getcwd(), 'legal/output/cms_npi/%s/'%folder_date_name)
                    make_dir(csv_processed_path)
                    csv_processed = csv_processed_path + item
                    try:
                        rename_file = csv_processed_path + 'CMS_NPPES_US_' + item
                        shutil.copy(zip_, csv_processed)
                        os.rename(csv_processed,rename_file)
                    except Exception as e:
                        print(e)

            data = {'last_modified_at' : str(date_time)}
        else:
            data = {'last_modified_at': from_db_last_date}
        yield data


class CmsnpaListingSpider(BaseSpider):
    name = SOURCE + '_listing_terminal'
    source_name = SOURCE
    MODEL = 'ListingTerminal'
    main_page_class = MainPage
