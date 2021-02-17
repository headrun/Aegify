import sys, os
sys.path.insert(1, os.getcwd())

import logging, traceback
from optparse import OptionParser
from datetime import timedelta

from django.utils import timezone
from django.db.models import Min, Max

from base.settings import DjangoUtil;DjangoUtil.setup()
from base.utils import standalone_main, init_logger, close_logger, import_module_var

class DBCleaner:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self):
        parser = OptionParser()
        self.add_parser_options(parser)
        (self.options, args) = parser.parse_args()

        self.init()

    def add_parser_options(self, parser):
        parser.add_option("-d", "--debug", dest="debug", help="Debug logs", default=False, action='store_true')

        parser.add_option("-a", "--app-models", dest="app_models", default='', help="app models path. default is ${SCRAPY_PROJECT}.models.")
        parser.add_option("",   "--crawlrun-expiry-days", dest="crawlrun_expiry_days", type=int, default=0, help="To delete expired CrawlRuns.")

    def init(self):
        models = self.options.app_models if self.options.app_models else '%s.models' % os.environ['SCRAPY_PROJECT']
        self.app_models = import_module_var(models, None)
        if not self.app_models:
            raise Exception('Unable to import module: %s' % models)

        model_name = 'CrawlRun'
        self.crawlrun_model = getattr(self.app_models, model_name, None)
        if not self.crawlrun_model:
            raise Exception('crawlrun model does not exist: %s.%s' % (self.app_models, model_name))

        if self.options.crawlrun_expiry_days <= 0:
            raise Exception('Invalid value for option crawlrun-expiry-days')

        self.log = init_logger(
            os.path.join(os.path.splitext(__file__)[0] + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )

    def process(self):
        self.log.info('Start: CrawlRun Ids: %s' % (self.crawlrun_model.objects.aggregate(min=Min('id'), max=Max('id'))))

        cutoff_datetime = timezone.now() - timedelta(days=self.options.crawlrun_expiry_days)
        self.log.info('Deleted CrawlRuns: %s', self.crawlrun_model.objects.filter(updated_at__lt=cutoff_datetime).delete())

        self.log.info('End: CrawlRun Ids: %s' % (self.crawlrun_model.objects.aggregate(min=Min('id'), max=Max('id'))))

    def close(self):
        close_logger(self.log)

if __name__ == '__main__':
    standalone_main(DBCleaner)
