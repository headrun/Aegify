from urllib.parse import urljoin, urlencode

from scrapy.http import Request, FormRequest
from scrapy.selector import Selector

from crawl.scrapy.validators import OKSchemaItem
from crawl.scrapy.spiders.base import BaseSpider
from crawl.scrapy.spiders.browse import BasePage, BrowseSpider
import time, os

SOURCE = 'cms_npi'
domain_url = 'https://download.cms.gov/nppes'

def delete_older_files(path):
    now = time.time()
    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.stat(f).st_mtime < now - 15 * 86400:
            if os.path.isfile(f):
                os.remove(os.path.join(path, f))
