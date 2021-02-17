from .base import *
from ..exceptions import FalsePositiveException

class BatchPage(BasePage):
    def __init__(self, *args, **kwargs):
        self.data_list = []
        super().__init__(*args, **kwargs)

    def parse(self, response):
        return self.data_list

    def add_data(self, key, obj):
        self.data_list.append(self.spider.get_batch_item(key, obj))

    def get_data_list(self):
        return self.data_list

class BatchMediaPage(MediaPage):
    def parse(self, response):
        obj = super().parse(response)
        return self.spider.get_batch_item(self.key, obj)

class BatchSpider(BaseSpider):

    def create_main_pages(self):
        batch_size = self.settings.get('BATCHSIZE', 1)
        for i in range(0, len(self.keys), batch_size):
            yield self.create_main_page(self.keys[i:i+batch_size])

    def create_main_page(self, keys):
        item_log_dict = {}
        for key in keys:
            item_log_dict[key] = self.create_item_log(self.item_model, key)

        page = self.main_page_class(None, spider=self, keys=keys, item_log_dict=item_log_dict)

        try:
            return self.create_request(page)
        except Exception as e:
            self.save_error(page, str(e))
            raise e

    def get_data(self, page, obj):
        key = obj['key']

        if isinstance(obj['data'], FalsePositiveException):
            super().save_error(page, str(obj['data']), item_log=page.item_log_dict[key], is_false_positive=True)
        else:
            data = super().get_data(page, obj['data'])
            data['key'] = key
            data['item_log'] = page.item_log_dict[key]
            return data

    def save_error(self, page, msg, item_log=None, is_false_positive=False):
        for key, item_log in page.item_log_dict.items():
            super().save_error(page, msg, item_log=item_log, is_false_positive=is_false_positive)

    def get_batch_item(self, key, obj):
        return {'key': key, 'data': obj}

    def handle_groups(self, obj):
        if isinstance(obj['data'], FalsePositiveException):
            return []
        groups = obj.get("data",{}).get("groups",[])
        keys_list = []
        for group in groups:
            for key in set(group.keys).difference(self.keys_set):
                if self.settings.get('GROUP_KEYS_CRAWL_ENABLED', False)==True:
                    self.keys_set.add(key)
                    keys_list.append(key)
                else:
                    item = self.create_item(self.item_model, key, self.source)

        batch_size = self.settings.get('BATCHSIZE', 1)
        keys_set   = keys_list
        for i in range(0, len(keys_set), batch_size):
            yield self.create_main_page(keys_set[i:i+batch_size])
