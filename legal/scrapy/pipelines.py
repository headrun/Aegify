# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from crawl.scrapy.pipelines import DjangoPipeline as BasePipeline

class DjangoPipeline(BasePipeline):
    def process_item(self, data, spider):
        super().process_item(data, spider)

    def update_item(self, item, data):
        item_data = data.get('data', {})
        if item_data and not item_data.get('name', None):
            item.status = 'Success'
        return super().update_item(item, data)
