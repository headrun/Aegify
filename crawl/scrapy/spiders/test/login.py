from scrapy.http import Request, FormRequest

from ..login import *
from . import base

class LoginMainPage(LoginPage):
    def request(self):
        data = {
            'username': self.username,
            'password': self.password,
        }
        return Request('http://localhost:8000/admin/login/?next=/admin/')

    def parse(self, response):
        return

class TestSpider(LoginSpider):
    name = 'login'
    source_name = 'test'

    login_page_class = LoginMainPage
    main_page_class = base.MainPage

