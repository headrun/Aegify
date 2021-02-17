from urllib.parse import urljoin, urlencode

from scrapy.http import Request, FormRequest
from scrapy.selector import Selector

from crawl.scrapy.validators import OKSchemaItem
from crawl.scrapy.spiders.base import BaseSpider
from crawl.scrapy.spiders.browse import BasePage, BrowseSpider
import os, time, sys

SOURCE = 'florida'
profile_data_xpath = '//li//a[contains(text(), "Profile Data Download")]//@href'


def add_url(link):
    url = 'https://mqa-internet.doh.state.fl.us/downloadnet/'
    return urljoin(url, link)


def delete_older_files(path):
    now = time.time()
    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.stat(f).st_mtime < now - 15 * 86400:
            if os.path.isfile(f):
                os.remove(os.path.join(path, f))
