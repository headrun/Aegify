import os
from importlib import import_module

class Util:
    NAME = ''

    @classmethod
    def settings_path(cls):
        return 'sites.%s.settings.%s' % (os.environ['SITE'], cls.NAME)

    @classmethod
    def settings(cls):
        return import_module(cls.settings_path())

    @classmethod
    def import_to(cls, module, var_dict):
        try:
            names = module.__all__
        except AttributeError:
            names = [name for name in module.__dict__ if not name.startswith('_')]
        var_dict.update({name: getattr(module, name) for name in names})

class DjangoUtil(Util):
    NAME = 'django'

    @classmethod
    def init(cls):
        os.environ['DJANGO_SETTINGS_MODULE'] = cls.settings_path()

    @classmethod
    def setup(cls):
        cls.init()

        from django import setup
        setup()

    @classmethod
    def init_sites(cls):
        from django.contrib.sites.models import Site

        for domain in os.environ['ENV_SITES'].split(' '):
            try:
                site = Site.objects.get(domain=domain)
            except Site.DoesNotExist:
                site = Site.objects.create(domain=domain, name=domain.split('.')[0].capitalize())

    @classmethod
    def get_absolute_url(cls, request, path):
        from urllib.parse import urlunsplit
        return urlunsplit([request.scheme, request.get_host(), path, '', ''])

class ScrapyUtil(Util):
    NAME = 'scrapy'

    @classmethod
    def init(cls, var_dict):
        cls.import_to(cls.settings(), var_dict)
