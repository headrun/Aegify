from base.settings.scrapy import *

ITEM_PIPELINES = {
    'legal.scrapy.pipelines.DjangoPipeline': 300,
}

