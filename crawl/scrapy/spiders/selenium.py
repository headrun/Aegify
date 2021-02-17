from .base import *
from scrapy.http import Request
GECKODRIVER_EXECUTABLE_PATH = os.environ.get(
    'ENV_GECKODRIVER_EXECUTABLE_PATH',
    '/usr/local/bin/geckodriver'   
)

class SeleniumRequest(Request):
    def __init__(self, url=None, wait_time=None, wait_until=None, screenshot=False, script=None, *args, **kwargs):
        """Initialize a new selenium request
        Parameters
        ----------
        wait_time: int
            The number of seconds to wait.
        wait_until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        script: str
            JavaScript code to execute.
        """

        self.wait_time = wait_time
        self.wait_until = wait_until
        self.screenshot = screenshot
        self.script = script

        super().__init__(url, *args, **kwargs)



class SeleniumPage(BasePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.browse_item = kwargs['item_log'].item

class SeleniumSpider(BaseSpider):
    MODEL = 'Browse'
    custom_settings = {
        #'SELENIUM_DRIVER_NAME': 'firefox',
        #'SELENIUM_DRIVER_EXECUTABLE_PATH': GECKODRIVER_EXECUTABLE_PATH,
        #'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
        'DOWNLOADER_MIDDLEWARES': {'crawl.scrapy.middlewares.selenium_middleware.SeleniumMiddleware': 800}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.init_items()
        self.item_source_dict = {}

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

    def init_items(self):
        try:
            objs = getattr(self.item_model, 'items', None)
            if not objs:
                raise Exception('Incompatible spider used for model %s' % self.item_model)

            self.save_item_model = objs.field.related_model
        except:
            pass

    def yield_item(self, page, source_name, key, obj, **kwargs):
        kwargs = self.create_related_item(page, source_name, key, obj, **kwargs)
        objs = obj if isinstance(obj, list) or isinstance(obj, types.GeneratorType) else [obj]
        for obj in objs:
            yield self.create_related_item_page(page, obj, **kwargs)

    def get_item(self, page, source_name, key, obj, **kwargs):
        for o in self.yield_item(page, source_name, key, obj, **kwargs):
            return o

    def create_related_item(self, page, source_name, key, obj, **kwargs):
        save_item_log = self.create_item_log(
                    self.save_item_model,
                    key,
                    source=self.get_item_source(source_name),
                    **kwargs
                )

        self.add_item(page, save_item_log, **kwargs)

        kwargs.update(self.get_key_dict(key))
        kwargs['item_log'] = save_item_log
        return kwargs

    def create_related_item_page(self, page, obj, **kwargs):
        if isinstance(obj, BasePage):
            obj.set_kwargs(kwargs)
            return obj
        else:
            return DataPage(page, obj, **kwargs)

    def get_item_source(self, source_name):
        source = None

        if source_name:
            if source_name not in self.item_source_dict:
                self.item_source_dict[source_name] = source = self.source_model.get_or_create_by_name(source_name, self.debug)
        return self.item_source_dict[source_name]

    def add_item(self, page, save_item_log, **kwargs):
        if self.save_item_model != self.item_model:
            page.item_log.item.items.add(save_item_log.item)
