from scrapy.http import Request, FormRequest

from ..user import *

from . import base

class LoginMainPage(UserLoginPage):
    def request(self):
        return Request('http://localhost:8000/admin/')

    def parse(self, response):
        return LoginNextPage(self, item_log=self.item_log)

class LoginNextPage(LoginMainPage):
    def request(self):
        data = {
            'username': self.username,
            'password': self.password,
        }
        return Request('http://localhost:8000/admin/login/?next=/admin/', dont_filter=True)

    def parse(self, response):
        return MainPage(self)

class MainPage(base.MainPage):
    def parse(self, response):
        self.kwargs['active'] = False
        val = [
            self.spider.get_user_item(self, 'u1', ItemPage(self)),
            self.spider.get_user_item(self, 'u2', OKSchemaItem()),
        ]

        val.append(OKSchemaItem()) # for crawl user log.
        return val

class ItemPage(base.MainPage):
    def parse(self, response):
        self.kwargs['active'] = False
        return OKSchemaItem()

class TestSpider(UserSpider):
    name = 'user'
    source_name = 'test'

    main_page_class = LoginMainPage
