import sys, os
sys.path.insert(1, os.getcwd())

import logging, traceback
from optparse import OptionParser
from datetime import datetime
from operator import itemgetter

from scrapy.crawler import CrawlerProcess
from scrapy.utils.conf import arglist_to_dict
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import UsageError
from scrapyd_api import ScrapydAPI

from base.utils import standalone_main, init_logger, close_logger, import_module_var
from crochet import setup

print(get_project_settings())

class BaseItemProcess(CrawlerProcess):
    def __init__(self, *args, **kwargs):
        sys.path.insert(1, os.path.join(os.environ['SCRAPY_PROJECT'].replace('.', '/'), 'scrapy'))

        kwargs['settings'] = get_project_settings()
        super().__init__(*args, **kwargs)

    def parse(self, *args, **kwargs):
        self.celery_executor = kwargs.get('celery_executor', False)
        if self.celery_executor:
            setup()
            sys.argv = [__file__]
        parser = OptionParser()
        self.add_parser_options(parser)
        (self.options, args) = parser.parse_args()
        self.options.__dict__.update(kwargs)
        self.init()

        
    def add_parser_options(self, parser):
        parser.add_option("-d", "--debug", dest="debug", help="Debug logs", default=False, action='store_true')

        parser.add_option("",   "--name", dest="name", default='--', help="Name of the Crawl Process.")
        parser.add_option("", "--list-spiders", dest="list_spiders", help="print spider names", default=False, action='store_true')
        parser.add_option("", "--list-keys", dest="list_keys", help="print keys per spider", default=False, action='store_true')

        parser.add_option("-z", "--spider-source-map-list", dest="spiders_sources_list", help="print spider source mapping", default=False, action='store_true')

        parser.add_option("-a", "--app-models", dest="app_models", default='', help="app models path. default is ${SCRAPY_PROJECT}.models.")
        parser.add_option("-s", "--spiders", dest="spiders", default='', help="',' separated spider names.")
        parser.add_option("-k", "--keys", dest="keys", default='', help="',' separated item keys.")

        parser.add_option("",   "--limit", dest="limit", type=int, default=-1, help="No. of keys per Source to be crawled.")
        parser.add_option("",   "--offset", dest="offset", type=int, default=-0, help="No. of keys per Source to be crawled.")

        parser.add_option("",   "--crawl", dest="crawl", action='store_true', default=False, help="Crawl without keys.")
        parser.add_option("",   "--spider-arguments", dest="spider_arguments", action="append", default=[], metavar="NAME=VALUE", help="set spider argument (may be repeated)")
        parser.add_option("",   "--req-limit", dest="req_limit", type=int, default=-1, help="',' No. of requests per Source to be crawled.")

        parser.add_option("",   "--new", dest="new", action="store_true", default=False, help="Will process only uncrawled keys.")
        parser.add_option("",   "--all-keys", dest="all_keys", action="store_true", default=False, help="Will process all the keys.")

        parser.add_option("",   "--include-source-groups", dest="include_source_groups", default='', help="',' separated source group names.")
        parser.add_option("",   "--exclude-source-groups", dest="exclude_source_groups", default='', help="',' separated source group names.")

        parser.add_option("",   "--include-log-status", dest="include_log_status", default='', help="',' separated log status.")
        parser.add_option("",   "--exclude-log-status", dest="exclude_log_status", default='', help="',' separated log status.")

        parser.add_option("",   "--launch-scrapyd", dest="launch_scrapyd", default=False, action='store_true' ,help="Whether to redirect to scrapyd server or not")

        parser.add_option("",   "--crawl-prefix-spiders", dest="crawl_prefix_spiders", default='',
                          help="',' separated spiders prefix names.")
        parser.add_option("",   "--crawl-suffix-spiders", dest="crawl_suffix_spiders", default='',
                          help="',' separated spiders suffix names.")

        parser.add_option("",   "--exclude-prefix-spiders", dest="exclude_prefix_spiders", default='',
                          help="',' separated spiders prefix names.")
        parser.add_option("",   "--exclude-suffix-spiders", dest="exclude_suffix_spiders", default='',
                          help="',' separated spiders suffix names.")

    def init(self):
        if not self.options.debug and not self.options.name:
            raise Exception('Option --name is mandatory if --debug is not provided')
        models = self.options.app_models if self.options.app_models else '%s.models' % os.environ['SCRAPY_PROJECT']
        self.import_app_models = models
        self.app_models = import_module_var(models, None)
        if not self.app_models:
            raise Exception('Unable to import module: %s' % models)

        try:
            self.options.spider_arguments = arglist_to_dict(self.options.spider_arguments)
        except ValueError:
            raise UsageError("Invalid --spider-arguments value, use --spider-arguments NAME=VALUE", print_help=False)

        self.spider_names = set([name for name in self.options.spiders.split(',') if name])

        self.log = init_logger(
            os.path.join(__file__.rstrip('.py') + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )

        self.keys = self.comma_str_to_list(self.options.keys)

        self.include_source_groups = self.comma_str_to_list(self.options.include_source_groups)
        self.exclude_source_groups = self.comma_str_to_list(self.options.exclude_source_groups)

        self.include_log_status = self.comma_str_to_list(self.options.include_log_status)
        self.exclude_log_status = self.comma_str_to_list(self.options.exclude_log_status)

        self.crawl_prefix_spiders   = self.comma_str_to_list(self.options.crawl_prefix_spiders)
        self.crawl_suffix_spiders   = self.comma_str_to_list(self.options.crawl_suffix_spiders)

        self.exclude_prefix_spiders = self.comma_str_to_list(self.options.exclude_prefix_spiders)
        self.exclude_suffix_spiders = self.comma_str_to_list(self.options.exclude_suffix_spiders)

        if (self.include_source_groups and self.exclude_source_groups) or \
            (self.include_log_status and self.exclude_log_status):
                raise Exception('Only one of the include and exclude options is allowed')

        if (self.crawl_prefix_spiders and self.crawl_suffix_spiders) or \
            (self.exclude_prefix_spiders and self.exclude_suffix_spiders):
                raise Exception('Only one of the prefix and suffix options is allowed')

    def process(self):
        spiders = [self.spider_loader.load(name) for name in self.spider_loader.list() if not self.spider_names or name in self.spider_names]

        if self.options.list_spiders:
            scrapy_project = os.environ.get("SCRAPY_PROJECT")
            self.log.info("START...\n{} ALL SPIDERS : \n\n{}\n\n...END".format(
                scrapy_project,
                self.spider_names or self.spider_loader.list()),
            )
            return

        if self.options.spiders_sources_list:
            scrapy_project  = os.environ.get("SCRAPY_PROJECT")
            spider_src_dict = {spider.name: self.get_source_name(spider) for spider in spiders }
            sorted_data     = sorted(spider_src_dict.items(), key=itemgetter(1))
            spider_src_dict = {spider: source for (spider, source) in sorted_data}
            self.log.info(" START...\n{} ALL SPIDERS SOURCE-NAMES MAPPING : \n\n{}\n\n...END".format(
                scrapy_project,
                spider_src_dict),
            )
            return

        self.log.info('App Models:%s' % self.app_models)
        self.log.info('spiders: %s' % spiders)

        if self.crawl_prefix_spiders:
            spiders = self.get_prefix_or_suffix_spiders(
                        crawl_spiders_names=self.crawl_prefix_spiders,
                        spiders_objs=spiders)

        elif self.crawl_suffix_spiders:
            spiders = self.get_prefix_or_suffix_spiders(
                        crawl_spiders_names=self.crawl_suffix_spiders,
                        spiders_objs=spiders,
                        filter_type='endswith')

        if self.exclude_prefix_spiders:
            spiders = self.get_exclude_prefix_or_suffix_spiders(
                        exclude_spiders_names=self.exclude_prefix_spiders,
                        spiders_objs=spiders)
        elif self.exclude_suffix_spiders:
            spiders = self.get_exclude_prefix_or_suffix_spiders(
                        exclude_spiders_names=self.exclude_suffix_spiders,
                        spiders_objs=spiders,
                        filter_type='endswith')

        item_model_dict = {}
        for spider in spiders:
            model_name = getattr(spider, 'MODEL', 'Item')
            val = item_model_dict.get(model_name, None)
            if not val:
                item_model = getattr(self.app_models, model_name, None)
                if not item_model:
                    raise Exception('%s does not have %s model' % (self.app_models, model_name))

                source_model = item_model.source.field.related_model
                objs = source_model.active_objects.prefetch_related('groups')

                if self.include_source_groups:
                    objs = objs.filter(groups__name__in=self.include_source_groups)
                if self.exclude_source_groups:
                    objs = objs.exclude(groups__name__in=self.exclude_source_groups)

                source_dict = {obj.name: obj for obj in objs}

                item_model_dict[model_name] = (item_model, source_dict)

        for spider in spiders:
            model_name = getattr(spider, 'MODEL', 'Item')
            val = item_model_dict.get(model_name, None)
            if not val:
                self.log.info('Skipping spider = %s, model_name = %s is invalid.' % (spider.name, model_name))
                continue

            item_model, source_dict = val
            source_name = self.get_source_name(spider)
            source = source_dict.get(source_name, None)
            if not source:
                if self.options.debug:
                    source_model = item_model.source.field.related_model
                    source = source_model.get_or_create_by_name(source_name, self.options.debug)
                else:
                    self.log.info('Skipping spider = %s, source = %s.' % (spider.name, source_name))
                    continue

            
            if self.options.launch_scrapyd:
                self._launch_scrapyd(item_model, spider, source)
            else:
                self.crawl_source(item_model, spider, source)

        try:
            if not (self.celery_executor or self.options.launch_scrapyd):
                print("starting_the_reactor")
                self.start()
        except:
            traceback.print_exc()
            return 1

    def close(self):
        close_logger(self.log)

    def crawl_source(self, item_model, spider, source):
        source.set_group_values()
        spider.custom_settings = spider.custom_settings or {}
        spider.custom_settings.update(source.settings)

        crawler = self.create_crawler(spider)

        keys = self.keys if self.keys or self.options.crawl else self.get_keys(source.name, item_model)
        self.log.info('keys: {}'.format(keys))
        self.log.info('spider = %s, source = %s, No. of keys = %s' % (spider.name, source.name, len(keys)))
        if not self.options.list_keys and (keys or self.options.crawl):
            crawl_run_model = item_model.logs.field.model.crawl_run.field.related_model
            crawl_run = crawl_run_model.objects.create(source=source, name=self.options.name)

            crawl_run.stats = crawler.stats._stats
            d = self._crawl(crawler,
                debug=self.options.debug, req_limit=self.options.req_limit,
                crawl_run=crawl_run, item_model=item_model, keys=keys,
                **self.options.spider_arguments
            )

            d.addBoth(self.stats_callback, crawl_run=crawl_run)
            d.addCallback(self.callback, crawl_run, spider)
            d.addErrback(self.errback, crawl_run, spider)

    def _launch_scrapyd(self, item_model, spider, source):
        app_models = self.import_app_models
        model_name = getattr(spider, 'MODEL', 'Item')

        source.set_group_values()
        settings = spider.custom_settings or {}
        settings.update(source.settings)
        spider.custom_settings = settings

        keys = self.keys if self.keys or self.options.crawl else self.get_keys(source.name, item_model)
        self.log.info('spider = %s, source = %s, No. of keys = %s' % (spider.name, source.name, len(keys)))
        scrapyd = ScrapydAPI(os.environ.get('SCRAPYD_SERVER', 'http://localhost:6800'))
        
        crawl_run_model = item_model.logs.field.model.crawl_run.field.related_model
        crawl_run = crawl_run_model.objects.create(source=source, name=self.options.name)

        item_model = '{app_models}.{model_name}'.format(app_models=app_models, model_name=model_name)
        job_id = scrapyd.schedule(os.environ['SCRAPY_PROJECT'], spider.name,
                     settings=settings, debug=self.options.debug,
                     req_limit=self.options.req_limit, crawl_run=crawl_run,
                     item_model=item_model, keys=','.join(keys),
                     **self.options.spider_arguments
                )
        self.log.info('job_id: {}'.format(job_id))

    def stats_callback(self, result, crawl_run):
        for key, val in crawl_run.stats.items():
            if isinstance(val, datetime):
                crawl_run.stats[key] = str(val)
        return result

    def callback(self, result, crawl_run, spider):
        crawl_run.status = crawl_run.STATUS_SUCCESS
        crawl_run.save()

        self.log.info('Finished crawl_run = %s, spider = %s' % (crawl_run, spider))
        return result

    def errback(self, failure, crawl_run, spider):
        self.log.info('Error crawl_run = %s, spider = %s: %s' % (crawl_run, spider, failure.getTraceback()))

        crawl_run.status = crawl_run.STATUS_FAILURE
        crawl_run.msg = failure.value
        crawl_run.save()

        return failure

    def comma_str_to_list(self, val):
        return [x.strip() for x in val.split(',') if x.strip()] if val else []

    def get_source_name(self, spider):
        return spider.get_source_name() if hasattr(spider, 'get_source_name') else spider.name

    def get_keys(self, source_name, item_model):
        objs = self.get_key_objs(source_name, item_model)

        log_status_list = self.include_log_status or self.exclude_log_status
        if log_status_list:
            itemlog_model = item_model.logs.field.model

            val = objs.values_list(item_model.KEY_FIELD_NAME, 'log_id')
            log_ids = {
                        *itemlog_model.objects.filter(
                            id__in=[log_id for key, log_id in val if log_id],
                            status__in=[itemlog_model.STATUS_LIST.index(x) for x in log_status_list]
                        ).values_list('id', flat=True)
                    }

            if self.include_log_status:
                keys = [key for key, log_id in val if log_id in log_ids]
            elif self.exclude_log_status:
                keys = [key for key, log_id in val if log_id not in log_ids]

            if self.options.offset > 0:
                objs = keys[self.options.limit:self.options.offset + self.options.limit ] if self.options.limit > 0 else keys[:self.options.offset]
            elif self.options.limit > 0:
                objs = keys[:self.options.limit]
        else:
            if self.options.offset > 0:
                objs = objs[self.options.limit:self.options.offset + self.options.limit ] if self.options.limit > 0 else objs[:self.options.offset]
            elif self.options.limit > 0:
                objs = objs[:self.options.limit]
            keys = list(objs.values_list(item_model.KEY_FIELD_NAME, flat=True))

        return keys

    def get_prefix_or_suffix_spiders(self, crawl_spiders_names, spiders_objs, filter_type="startswith"):
        is_endswith, is_startswith = False, False
        if filter_type == "endswith":
            is_endswith = True
        elif filter_type == "startswith":
            is_startswith = True

        filtered_spiders = []
        for spider_name in crawl_spiders_names:
            for spider_obj in spiders_objs:
                if is_endswith and spider_obj.name.endswith(spider_name):
                    filtered_spiders.append(spider_obj)
                elif is_startswith and spider_obj.name.startswith(spider_name):
                    filtered_spiders.append(spider_obj)

        return filtered_spiders

    def get_exclude_prefix_or_suffix_spiders(self, exclude_spiders_names, spiders_objs, filter_type="startswith"):
        is_endswith, is_startswith = False, False
        if filter_type == "endswith":
            is_endswith = True
        elif filter_type == "startswith":
            is_startswith = True

        for spider_name in exclude_spiders_names:
            for spider_obj in spiders_objs:
                if is_endswith and spider_obj.name.endswith(spider_name):
                    spiders_objs.remove(spider_obj)
                elif is_startswith and spider_obj.name.startswith(spider_name):
                    spiders_objs.remove(spider_obj)

        return spiders_objs

    def get_key_objs(self, source_name, item_model):
        from django.db.models import Max

        objs = self.get_active_items(item_model)

        if not self.options.all_keys:
            objs = objs.filter(source__name=source_name)

        if self.options.new:
            objs = objs.filter(logs=None)

        objs = objs.annotate(log_id=Max('logs__id')).order_by('log_id', 'updated_at')

        return objs

    def get_active_items(self, item_model):
        return item_model.active_objects

if __name__ == '__main__':
    standalone_main(BaseItemProcess)
