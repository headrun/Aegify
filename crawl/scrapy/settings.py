from base.settings.scrapy import *

ITEM_PIPELINES = {
    'crawl.scrapy.pipelines.DjangoPipeline': 300,
}

FALSE_POSITIVE_EXPIRY_DAYS = 0
