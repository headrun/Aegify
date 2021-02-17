import sys, os
import socket
sys.path.insert(1, os.getcwd())

import logging, traceback
from optparse import OptionParser
from datetime import timedelta

from django.utils import timezone
from django.db.models import Q

from base.settings import DjangoUtil;DjangoUtil.setup()
from base.utils import standalone_main, init_logger, close_logger, import_module_var
from base.daily_mail_alerts import ItemStatus

class SlaAlert:
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
        parser.add_option("-s", "--sla-alert", dest="sla_alert", help="send the alert mail for sla failed", default=False)
        parser.add_option("-i", "--sla-alert-interval", dest="sla_alert_interval", help="Time Interval for verifying sla time", default=15, type=int)
        parser.add_option('-c', "--sla-crawl-name", dest="sla_crawl_name", default='--', help="To verify with crawlruns status")

    def init(self):
        models = self.options.app_models if self.options.app_models else '%s.models' % os.environ['SCRAPY_PROJECT']
        self.app_models = import_module_var(models, None)
        if not self.app_models:
            raise Exception('Unable to import module: %s' % models)

        model_name = 'CrawlRun'
        self.crawlrun_model = getattr(self.app_models, model_name, None)
        if not self.crawlrun_model:
            raise Exception('crawlrun model does not exist: %s.%s' % (self.app_models, model_name))

        if not self.options.sla_alert:
            raise Exception('Invalid value for option sla alert duration')

        self.log = init_logger(
            os.path.join(os.path.splitext(__file__)[0] + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )

    def process(self):
        site            = os.environ.get('SITE')
        host_name       = socket.gethostname()
        site_app_name   = os.environ.get('SCRAPY_PROJECT')

        if self.options.sla_alert:
            self.log.info('Start SLA Verification')
            cutoff_diff     = timezone.now()
            cutoff_datetime = timezone.now() - timedelta(minutes=self.options.sla_alert_interval)
            crawl_objects   = self.crawlrun_model.objects.filter(
                    Q(name=self.options.sla_crawl_name,
                    created_at__gt=cutoff_datetime,
                    created_at__lt=cutoff_diff)
                )
            if crawl_objects:
                subject = "SlaAlert: Failed for {} ".format(site_app_name)
                text    = '''<html>
                                <body>Hi Team, <br /> <br />
                                    Please check the latest crawlruns for {site}.<br />
                                    more info {stats} <br /> <br />
                                    Please look at the {app_name} crawlruns.
                                </body>
                            </html>'''.format(site=site,
                                            stats=str({
                                                "status":"failed to crawlrun {time_zone}".format(time_zone=timezone.now()),
                                                "host_name": host_name,
                                                "project_app": site
                                            }),
                                            app_name=site_app_name,
                                        )
                self.log.info("Mail Sent {}".format(text))
                ItemStatus.send_mail(self, subject=subject, text=text)
            else:
                self.log.info("CrawlRuns are running fine, SLA is good")

    def close(self):
        close_logger(self.log)

if __name__ == '__main__':
    standalone_main(SlaAlert)
