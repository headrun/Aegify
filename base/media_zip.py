import sys, os
sys.path.insert(1, os.getcwd())

import shutil
import zipfile
import logging
from optparse import OptionParser
from datetime import datetime

from base.settings import DjangoUtil;
settings = DjangoUtil.settings()

from base.utils import standalone_main, init_logger, close_logger, makedir_p

class BaseMediaZip:
    def parse(self):
        self.parser = OptionParser()
        self.add_parser_options(self.parser)
        (self.options, args) = self.parser.parse_args()

        self.init()
        
    def add_parser_options(self, parser):
        parser.add_option("-d", "--debug", dest="debug", help="Debug logs", default=False, action='store_true')

        parser.add_option("",   "--name", dest="name", default='', help="Name of the zip file.")

        parser.add_option("",   "--input-path", dest="input_path", default='', help="Relative path from MEDIA_ROOT")
        parser.add_option("",   "--output-path", dest="output_path", default='', help="Relative path from MEDIA_ROOT")
        parser.add_option("-t", "--timestamp", dest="timestamp", default=False, action='store_true', help="Unique Name of the zip file")

    def init(self):
        if not (self.options.name and self.options.input_path and self.options.output_path):
            self.parser.print_help()
            raise Exception('Invalid options')

        self.log = init_logger(
            os.path.join(__file__[:-3] + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )
        self.name = self.options.name
        if self.options.timestamp:
            self.name = self.options.name + "_" + self.get_timestamp()
        self.input_path = self.options.input_path
        self.output_path = self.options.output_path

        os.chdir(settings.MEDIA_ROOT)
        makedir_p(self.options.output_path)

    def process(self):
        filename = '%s.zip' % self.name
        self.create_zip_file(self.input_path, self.output_path, filename)

    def create_zip_file(self, input_path, output_path, filename):
        zip_filepath = os.path.join(output_path, filename)
        tmp_filepath = os.path.join(output_path, 'media_tmp.zip')
        self.log.info('Input path = %s, zip_filepath = %s, tmp_filepath = %s' % (input_path, zip_filepath, tmp_filepath))

        zip_fl = zipfile.ZipFile(tmp_filepath, 'w', zipfile.ZIP_DEFLATED)

        self.zip_dir(input_path, zip_fl)
        zip_fl.close()
        shutil.move(tmp_filepath, zip_filepath)
        self.log.info('Created filepath=%s' % zip_filepath)

    def zip_dir(self, root_dir, zip_fl):
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                zip_fl.write(os.path.join(root, file))

    def get_timestamp(self):
        return datetime.now().strftime('%d-%m-%Y-%H-%M-%S')

    def close(self):
        close_logger(self.log)

if __name__ == '__main__':
    standalone_main(BaseMediaZip)
