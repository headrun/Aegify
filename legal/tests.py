from django.test import SimpleTestCase

from crawl.tests import APIMixin

from .api import views

class TestCase(APIMixin, SimpleTestCase):
    view_module = views

