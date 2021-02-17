from .base import *

class LoginPage(BasePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__dict__.update(self.crawl_user.get_data())

        if not (self.username or self.password):
            raise Exception('Invalid username = %s and password = %s' % (self.username, self.password))

class LoginSpider(BaseSpider):
    custom_settings = {'COOKIES_ENABLED': True}    

    login_page_class = None
    AUTHENTICATE = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.crawl_user = None
        if not self.AUTHENTICATE:
            return

        objs = getattr(self.item_model, 'crawl_users', None)
        if not objs:
            raise Exception('Incompatible spider used for model %s' % self.item_model)

        self.crawl_user = objs.field.model.random_user(self.source)
        if not self.crawl_user:
            raise Exception('No Valid users for source = %s' % self.source)

    def start_requests(self):
        page = self.login_page_class(None, spider=self, crawl_user=self.crawl_user)

        try:
            yield self.create_request(page)
        except Exception as e:
            self.save_error(page, str(e))
            raise e

    def handle_data(self, page, obj):
        if issubclass(page.__class__, LoginPage) and obj == None:
            return self.create_main_pages()

        return super().handle_data(page, obj)
