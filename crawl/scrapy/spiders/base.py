import os, random, types
from datetime import timezone, timedelta

from scrapy import Spider
from scrapy.http import Request

from base.utils import import_module_var, get_media_url

from ..validators import *
from ..exceptions import FalsePositiveException

class BasePage:
    def __init__(self, parent_page, **kwargs):
        self.req = self.callback = None
        self.parent_page = parent_page

        self.kwargs = {}
        if parent_page:
            self.set_kwargs(parent_page.kwargs)
        self.set_kwargs(kwargs)

        if self.req:
            self.callback = self.req.callback

    def request(self):
        return self.req

    def errback(self, response):
        return

    def parse(self, response):
        callback = self.callback or self.spider.parse_main
        limit = getattr(self.spider, 'req_limit', -1)
        for obj in callback(response):
            yield obj
            limit -= 1
            if limit == 0:
                break

    def set_kwargs(self, kwargs):
        self.kwargs.update(kwargs)
        self.__dict__.update(kwargs)

class DataPage(BasePage):
    def __init__(self, parent_page, obj, **kwargs):
        self.obj = obj
        super().__init__(parent_page, **kwargs)

    def request(self):
        return self.spider.get_data(self, self.obj)

class MediaPage(BasePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.media_path = get_media_url(os.path.join(self.spider.get_source_name(), self.key, self.path))

    def request(self):
        return Request(self.url, headers=self.headers)

    def parse(self,response):
        return {'path': self.media_path, 'data': response.body}

class BaseSpider(Spider):
    main_page_class = BasePage

    @classmethod
    def get_source_name(cls):
        return getattr(cls, 'source_name', cls.name)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

            
        self.item_model = kwargs.get('item_model', None)
        if isinstance(self.item_model, str):
            self.item_model = import_module_var(self.item_model, None)
        
        self.crawl_run = kwargs.get('crawl_run', None)

        if isinstance(self.crawl_run, str):
            crawl_run_model = self.item_model.logs.field.model.crawl_run.field.related_model
            self.crawl_run = crawl_run_model.objects.get(id=self.crawl_run)
        
        self.source_model   = self.item_model.source.field.related_model

        self.source = self.source_model.objects.select_related('proxy').prefetch_related('groups').get(name=self.get_source_name())
        self.source.set_group_values()

        self.keys = kwargs.get('keys', [])
        if isinstance(self.keys, str):
            if self.keys[0] == '[':
                self.keys = eval(self.keys)
            else:
                self.keys = [x for x in self.keys.split(',') if x]
        self.keys_set = set(self.keys)

    def start_requests(self):
        return self.create_main_pages()

    def create_main_pages(self):
        func = getattr(self, 'start_requests_main', super().start_requests)
        for req in func():
            yield self.create_main_page(req.url, req=req)

        for key in self.keys:
            yield self.create_main_page(key)

    def create_main_page(self, key, **kwargs):
        item_log = self.create_item_log(self.item_model, key)
        if 'url' not in kwargs:
            kwargs['url'] = item_log.item.url

        page = self.main_page_class(None, spider=self, key=key, item_log=item_log, **kwargs)

        try:
            return self.create_request(page)
        except Exception as e:
            self.save_error(page, str(e))
            raise e

    def errback(self, response):
        page = response.request.meta['page']
        obj = page.errback(response)
        if obj:
            return self.get_data(page, obj)

        msg = str(response.value.response.status if hasattr(response.value, 'response') else str(response.value))
        self.save_error(page, msg)

    def parse(self, response):
        limit = getattr(self, 'req_limit', -1)
        page = response.meta['page']
        try:
            obj = page.parse(response)
            objs = obj if isinstance(obj, list) or isinstance(obj, types.GeneratorType) else [obj]
            for obj in objs:
                if isinstance(obj, BasePage):
                    yield self.create_request(obj)
                    limit -= 1
                elif isinstance(obj, Request):
                    yield self.create_request(self.main_page_class(page, req=obj))
                    limit -= 1
                elif isinstance(obj, BaseSchemaItem) or \
                        isinstance(obj, dict):
                    for o in self.handle_groups(obj):
                        yield o
                    yield self.get_data(page, obj)
                else:
                    for o in self.handle_data(page, obj):
                        yield o

                if limit == 0:
                    break
        except Exception as e:
            self.save_error(page, str(e), is_false_positive=isinstance(e, FalsePositiveException))
            raise e

    def create_request(self, page):
        req = page.request()
        if isinstance(req, dict):
            return req

        if req:
            req.meta['page'] = page
            req.headers.update(self.source.headers)
            self.init_proxy(req, self.source.proxy)

            req.callback = self.parse
            req.errback = self.errback
            return req

    def get_data(self, page, obj):
        data = {'source': self.get_source_name(), 'data': obj}
        data.update(page.kwargs)
        return data

    def handle_data(self, page, obj):
        raise Exception('BasePage.parse must return BasePage, BaseSchemaItem or dict. page %s returned %s' % (page, obj))

    def handle_groups(self, obj):
        groups = obj.get('groups', [])
        for group in groups:
            for key in set(group.keys).difference(self.keys_set):
                if self.settings.get('GROUP_KEYS_CRAWL_ENABLED',False)==True:
                    self.keys_set.add(key)
                    yield self.create_main_page(key)
                else:
                    item = self.create_item(self.item_model, key, self.source)

    def get_key_dict(self, key, **kwargs):
        key_dict = key if isinstance(key, dict) else {'key': key}
        key_dict.update(kwargs)
        return key_dict

    def create_item(self, item_model, key, source=None, **kwargs):
        item, flag = item_model.latest_get_or_create(source=source, **self.get_key_dict(key))
        item.source = source
        if kwargs:
            item.__dict__.update(kwargs)
            item.save()
        return item

    def create_item_log(self, item_model, key, source=None, **kwargs):
        source = source if source else self.source
        item = self.create_item(item_model, key, source, **kwargs)

        if kwargs.get('parent_source', None) and kwargs.get('browse_item', None):
            item_model = self.item_model
            item = self.create_item(item_model, kwargs['browse_item'], self.source, **kwargs)

        itemlog_model  = item_model.logs.field.model
        return itemlog_model.objects.create(crawl_run=self.crawl_run, item=item, spider=self.name)

    def init_proxy(self, req, proxy):
        if not proxy:
            return
        req.meta['proxy'] = random.choice(proxy.servers)
        if proxy.headers:
            for name, value in proxy.headers.items():
                req.headers[name] = value

    def save_error(self, page, msg, item_log=None, is_false_positive=False):
        msg = page.__class__.__name__ + ':' + msg

        item_log = item_log if item_log else getattr(page, 'item_log', None)
        if not item_log:
            return
        item_log.status = item_log.STATUS_FALSEPOSITIVE  if is_false_positive else item_log.STATUS_FAILURE
        item_log.msg    = item_log.msg + ('\n' if item_log.msg else '') + msg
        item_log.save()

        if is_false_positive:
            item = item_log.item
            expired = False
            if getattr(self, 'unknown', None):
                expired = True
            else:
                d = self.settings.get('FALSE_POSITIVE_EXPIRY_DAYS', 0)
                if d and not item.data_list.count() and item.created_at + timedelta(days=d) < timezone.now():
                    expired = True

            if expired:
                item.active = False
                item.save()
