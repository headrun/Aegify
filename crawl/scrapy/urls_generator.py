import sys
import os
import logging
sys.path.insert(1, os.getcwd())

from optparse import OptionParser

from base.settings import DjangoUtil;DjangoUtil.setup()
from base.utils import standalone_main, init_logger, close_logger, import_module_var

class ItemGenerator:
    def parse(self):
        self.parser = OptionParser()
        self.add_parser_options(self.parser)
        (self.options, args) = self.parser.parse_args()
        self.init()

    def add_parser_options(self, parser):
        parser.add_option("-d", "--debug", dest="debug", help="Debug logs",\
            default=False, action='store_true')
        parser.add_option("-a", "--app-models", dest="app_models", \
            default='', help="app models path. default is ${SCRAPY_PROJECT}.models.")
        parser.add_option("-m", "--model-name", dest="model_name", default="Item",\
            type=str, help="To insert the generated items")

        parser.add_option("-s", "--source-name", dest="source_name", default='', \
            help="To map the generated items")
        parser.add_option("-u", "--base-url", dest="base_url", default='', \
            help="to format the items")
        parser.add_option("-i", "--start-pointer", dest="start_pointer", default=0, \
            type=int, help="Start pointer to generate url-items")
        parser.add_option("-e", "--end-pointer", dest="end_pointer", default=0, type=int,\
            help="End pointer to generate url-items")
        parser.add_option("-l", "--load-data", dest="load_data", default=False, \
            action="store_true", help="loading into the db")
        parser.add_option("-k", "--item-temp-key", dest="item_temp_key", default='', \
            help="To instert as temp key name")

    def init(self):
        self.log = init_logger(
            os.path.join(__file__[:-3] + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )

    def process(self):
        models = self.options.app_models if self.options.app_models \
            else '%s.models' % os.environ['SCRAPY_PROJECT']
        app_models = import_module_var(models, None)
        item_model = getattr(app_models, self.options.model_name, None)
        source_model = getattr(app_models, 'Source', None)
        parsed_items = self.get_format_urls()
        if self.options.load_data and self.options.source_name:
            src_obj, is_created = source_model.objects.get_or_create(name=self.options.source_name)
            for item in parsed_items:
                try:
                    item_key = parsed_items.get(item)
                    if self.options.item_temp_key:
                        item_key = self.options.item_temp_key + str(item_key)

                    item_model.objects.get_or_create(source=src_obj,
                                        url=item,
                                        key=item_key)
                except Exception as err:
                    self.log.info("Unable to load the item {} {}".format(str(err), str(item)))

    def get_format_urls(self):
        if not (self.options.end_pointer or self.options.start_pointer):
            raise Exception('Unable to format the urls, Please provide the range')
        if not self.options.base_url:
            raise Exception('Unable to format the urls, Please provide the BASE_URL')
        return {
            self.options.base_url + str(url_pointer): str(url_pointer) for url_pointer in \
            list(range(self.options.start_pointer, self.options.end_pointer))
        }

    def close(self):
        close_logger(self.log)

if __name__ == '__main__':
    standalone_main(ItemGenerator)
