import csv
import json
import logging

from urllib.parse import unquote
from inspect import ismethod
from io import TextIOWrapper

from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.mixins import UpdateModelMixin
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import ( HTTP_204_NO_CONTENT,
                            HTTP_200_OK,
                            HTTP_404_NOT_FOUND)
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.views import APIView

from base.settings import DjangoUtil;
settings = DjangoUtil.settings()

from ..scrapy.launcher import Launcher

log = logging.getLogger(__name__)

def url_prefix(version):
    return r'v%d/' % version

def model(obj):
    if hasattr(obj, 'model'):
        return obj.model
    else:
        m = getattr(obj, 'get_serializer_class', None)
        if ismethod(m):
            return m().Meta.model
        elif hasattr(obj, 'serializer_class'):
            return obj.serializer_class.Meta.model

def api_name(obj):
    return model(obj).api_name()

def app_label(obj):
    return model(obj)._meta.app_label

def url_name(obj, name):
    return app_label(obj) + '_' + model(obj)._meta.model_name + ('_' + name if name else name)

class APIPermission(IsAuthenticatedOrTokenHasScope):
    def has_permission(self, request, view):
        ret = super().has_permission(request, view)
        return request.user.is_staff if request.user and request.user.is_authenticated else ret


class CsvResultsSetPagination(PageNumberPagination):
    ordering = 'updated_at'
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class CrawlCursorPagination(CursorPagination):
    ordering = 'updated_at'
    page_size_query_param = 'page_size'
    page_size = 10
    max_page_size = 100

class UrlMixin:
    permission_classes = [APIPermission] if not settings.DEBUG else []

    @classmethod
    def get_url(self, *args):
        return reverse(url_name(self, self.view_name), args=args)

    @classmethod
    def urlpatterns(self, version):
        name = url_name(self, self.view_name)
        prefix = url_prefix(version) + api_name(self) + self.url_path
        return [
            url(prefix, self.as_view(), name=name),
        ]

class SourceKeyMixin:
    lookup_field = 'key'
    lookup_url_kwarg = 'key'

    def get_queryset(self):
        self.kwargs[self.lookup_url_kwarg] = unquote(self.kwargs.get(self.lookup_url_kwarg, ''))

        source_name = self.get_source_name()
        objs = self.get_manager().select_related('source')
        if source_name:
            objs = objs.filter(Q(source__name=source_name) | Q(source__aka=source_name))
        return objs

    def get_manager(self):
        return model(self).latest_objects

    def get_source_manager_objs(self):
        return model(self).source.field.related_model.objects

    def get_source_name(self):
        return self.kwargs.get('source_name', self.kwargs.get('source', {}).get('name', ''))

    def get_key(self):
        return self.kwargs.get(self.lookup_url_kwarg, '')

    def set_kwargs(self, req_data):
        pass

    def update_source_kwarg(self, param_name):
        if param_name in self.kwargs:
            self.kwargs['source'] = {'name': self.kwargs.pop(param_name)}

class ListCreateUpdateView(UrlMixin, SourceKeyMixin, UpdateModelMixin, ListCreateAPIView):
    required_scopes = ['write']
    pagination_class = CrawlCursorPagination

    url_path = '/$'
    view_name = 'listcreate'

    def get(self, request, *args, **kwargs):
        try:
            self.set_kwargs(request.query_params)
            if request.query_params.get('required_csv') == 'true':
                self.pagination_class = CsvResultsSetPagination
                resp_data = super().list(request, *args, **kwargs)
                response = HttpResponse(content_type='text/csv')
                try:
                    file_name = self.get_url().split('/')[-2]
                except:
                    file_name = 'ItemData'
                response['Content-Disposition'] = 'attachment; filename="%s.csv"'%file_name
                resp = self.get_csv_response(resp_data, response)
            else:
                resp = super().list(request, *args, **kwargs)
        except:
            resp = HttpResponseBadRequest()

        return resp

    def post(self, request, *args, **kwargs):
        try:
            self.set_kwargs(request.data)

            if not self.get_source_name() or not self.get_key():
                resp = HttpResponseBadRequest()
            else:
                resp = self.update(request, *args, **kwargs)
        except Http404:
            try:
                resp = self.create(request, *args, **kwargs)
            except model(self).source.field.related_model.DoesNotExist:
                resp = HttpResponseBadRequest()
        except model(self).MultipleObjectsReturned:
            resp = HttpResponseBadRequest()

        log.info('%s %s %s: %s' % (request.method, request.path, dict(request.data), resp.status_code))
        return resp

    def put(self, request):
        result = []
        try:
            data = self.get_csv_data_list(request)
        except:
            return Response(status=HTTP_404_NOT_FOUND)
        for da in data:
            _, created = model(self).objects.update_or_create(**da)
        return Response(status=HTTP_200_OK)

    def get_csv_response(self, resp, response):
        results = resp.data.get('results',[])
        if results:
            results = json.loads(json.dumps(results))
            fnames = resp.data['results'][0].keys()
            writer = csv.DictWriter(response, fieldnames=fnames)
            for da in results:
                writer.writerow(da)

        return response

    def get_csv_data_list(self, request):
        f = TextIOWrapper(request.FILES['file'].file, encoding=request.encoding)
        csvfile = csv.DictReader(f, delimiter=',')
        source_ids = {i.name: i.id for i in model(self).source.get_queryset()}
        data = []
        for row in csvfile:
            try:
                row['source_id'] = source_ids[row['source.name']]
                row['active'] = eval(row['active'])
                del row['source.name']
            except:
                continue
            data.append(row)
        return data

    def get_key(self):
        key = super().get_key()
        return key if model(self).is_valid_key(key) else None

    def set_kwargs(self, req_data):
        self.kwargs.update(req_data.items())

        self.update_source_kwarg('source.name')

class DetailView(UrlMixin, SourceKeyMixin, RetrieveAPIView):
    required_scopes = ['read']

    url_path ='/(?P<source_name>[-\.\w]+)/(?P<key>[%-\.\w\s]+)/$'
    view_name = ''

    SCRAPY_PROJECT = None
    SPIDER_ALIAS = None

    @classmethod
    def urlpatterns(self, version):
        return format_suffix_patterns(super().urlpatterns(version))

    def get_object(self):
        try:
            if self.crawl_now:
                instance = self.crawl(None, self.get_object)
            else:
                instance = super().get_object()
        except Http404 as e:
            instance = self.crawl(None, self.get_object)
            if not instance:
                raise e

        return instance

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.data_params = self.get_data_params()
        try:
            data = serializer.data['data']
        except:
            return serializer

        new_serializer = self.crawl(data, self.get_serializer, args, kwargs)
        if new_serializer:
            serializer = new_serializer
            data = serializer.data['data']

        if not data or data.get('http_status', None):
            e = model(self).InvalidDataException()
            e.http_status = data.get('http_status', HTTP_204_NO_CONTENT)
            raise e
        return serializer

    def retrieve(self, request, *args, **kwargs):
        try:
            self.set_kwargs(request.query_params)

            return super().retrieve(request, *args, **kwargs)
        except ObjectDoesNotExist as obj_does_exist_err:
            return Response(status=HTTP_404_NOT_FOUND)
        except model(self).InvalidDataException as e:
            return Response(status=e.http_status)

    def get_data_params(self):
        return dict(self.request.GET.items())

    def set_kwargs(self, req_data):
        super().set_kwargs(req_data)

        self.crawl_now = req_data.get('crawl_now', '') == 'true'
        self.crawl_if_empty = req_data.get('crawl_if_empty', '') == 'true'

        try:
            crawl_retry_limit = int(req_data.get('crawl_retry_limit'))
            crawl_retry_limit = max(crawl_retry_limit, 0)
            self.crawl_retry_limit = min(10, crawl_retry_limit)
        except:
            self.crawl_retry_limit = 0

        try:
            self.crawl_timeout = int(req_data.get('crawl_timeout'))
        except:
            self.crawl_timeout = Launcher.DEFAULT_CRAWL_TIMEOUT_SECONDS

    def crawl(self, crawl_data, cb_fn, cb_args=[], cb_kwargs={}):
        if self.is_invalid_crawl_data(crawl_data) \
                and (self.crawl_now or self.crawl_if_empty) \
                and self.crawl_retry_limit >= 0:

            launcher = self.get_launcher()
            launcher.crawl()

            self.crawl_retry_limit -= 1
            return cb_fn(*cb_args, **cb_kwargs)

    def is_invalid_crawl_data(self, crawl_data):
        return not crawl_data

    def get_launcher(self):
        launcher = getattr(self, 'launcher', None)
        if not launcher:
            item_model = self.get_item_model()
            item_model_path = '%s.%s' % (item_model.__module__, item_model.__name__)

            spider = self.get_spider_name()
            settings = self.get_spider_settings()

            launcher = Launcher()
            launcher.init(self.SCRAPY_PROJECT, spider, settings, item_model_path, [self.get_key()], self.crawl_timeout)
        return launcher

    def get_item_model(self):
        return self.get_serializer_class().Meta.model

    def get_spider_name(self):
        return self.get_source_name().lower() + "_" + self.SPIDER_ALIAS

    def get_spider_settings(self):
        item_model = self.get_item_model()
        source_model = item_model.source.field.related_model
        source = source_model.objects.get(name=self.get_source_name(), active=True)
        source.set_group_values()
        return {key: json.dumps(value) for key, value in source.settings.items()}

class DetailListView(UrlMixin, SourceKeyMixin, ListAPIView):
    required_scopes = ['read']

    url_path = '/(?P<key>[%-\.\w\s]+)/$'
    view_name = 'keylist'

    @classmethod
    def urlpatterns(self, version):
        return format_suffix_patterns(super().urlpatterns(version))

    def get_queryset(self):
        objs = super().get_queryset()
        return objs.select_related('source').prefetch_related('data_list').filter(key=self.get_key())

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.child.data_params = self.get_data_params()
        return serializer

    def list(self, request, *args, **kwargs):
        self.set_kwargs(request.query_params)

        resp = super().list(request, *args, **kwargs)

        return resp if resp.data else Response(status=HTTP_404_NOT_FOUND)

    def get_data_params(self):
        return dict(self.request.GET.items())

    def get_manager(self):
        return model(self).objects
