import sys, os
sys.path.insert(1, os.getcwd())

import logging
import xlsxwriter

from optparse import OptionParser

from base.settings import DjangoUtil;
settings = DjangoUtil.settings()

from base.utils import standalone_main, init_logger, close_logger

class BaseFile:
    def __init__(self, filename):
        self.filename = filename
        # self.filehandler = open(self.filename,'w+')

    def write(self, data):
        pass

    def close(self):
        pass

class JsonFile(BaseFile):
    def __init__(self, filename):
        BaseFile.__init__(self, filename)

    def write(self, data):
        print(self.filename, data)

class XlsxFile(BaseFile):
    def __init__(self, filename):
        BaseFile.__init__(self, filename)
        self.filehandler = xlsxwriter.Workbook(self.filename)
        self.worksheet = self.filehandler.add_worksheet()
        self.row = self.col = 0

    def write_row(self, data):
        self.worksheet.write_row(self.row,self.col, data)
        self.row += 1

    def write(self, data):
        self.write_row(data.values())
        
    def close(self):
        self.filehandler.close()
        
        

class BaseDataDump:
    def parse(self):
        self.parser = OptionParser()
        self.add_parser_options(self.parser)
        (self.options, args) = self.parser.parse_args()

        self.init()
        
    def add_parser_options(self, parser):
        parser.add_option("-d", "--debug", dest="debug", help="Debug logs", default=False, action='store_true')

        parser.add_option("",   "--format", dest="format", default='json', help="File Format. ex., json, xlsx")
        parser.add_option("",   "--batch-size", dest="batch_size", default=-1, type=int, help="Batch size")
        parser.add_option("",   "--num-batches", dest="num_batches", default=-1, type=int, help="Number of batches.")

    def init(self):
        if not (self.options.batch_size):
            self.parser.print_help()
            raise Exception('Invalid Batch Size')

        if not (self.options.num_batches):
            self.parser.print_help()
            raise Exception('Invalid Number of Batches')

        self.log = init_logger(
            os.path.join(__file__[:-3] + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )

    def process(self):
        fl = self.create_file()

        offset = 0
        batch_size = self.options.batch_size
        num_batches = self.options.num_batches
        while True:
            if offset:
                print("Completed writing "+str(offset)+" records")

            objs = self.get_batch_objs(offset, batch_size)
            if len(objs) == 0:
                break

            for obj in objs:
                fl.write(self.get_serializer_class()(obj).data)
                
            offset += batch_size
            if num_batches > 0:
                num_batches -= 1
                if num_batches == 0:
                    break

        fl.close()

    def close(self):
        close_logger(self.log)

    def get_batch_objs(self, offset, batch_size):
        return []

    def create_file(self):
        filename = self.get_filename()
        if self.options.format == 'json':
            return JsonFile(filename)
        elif self.options.format == 'xlsx':
            return XlsxFile(filename)

        raise Exception('Invalid Format')

    def get_filename(self):
        return __file__[:-3] + '.out'

    def get_serializer_class(self):
        return

if __name__ == '__main__':
    standalone_main(BaseDataDump)
