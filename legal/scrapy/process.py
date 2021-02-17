import sys, os
sys.path.insert(1, os.getcwd())

from crawl.scrapy.process import *

class ItemProcess(BaseItemProcess):
    def add_parser_options(self, parser):
        super().add_parser_options(parser)

if __name__ == '__main__':
    standalone_main(ItemProcess)
