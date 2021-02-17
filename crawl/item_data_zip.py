import sys, os
sys.path.insert(1, os.getcwd())
import json
from base.settings import DjangoUtil
from base.media_zip import *
from base.utils import makedir_p, import_module_var
DjangoUtil.setup()

class ItemDataZIP(BaseMediaZip):
    def add_parser_options(self, parser):
        parser.add_option("-s", "--serializers", dest="serializers",
                          default=None, help="comma,separated serilaizers to get item data.")
        super().add_parser_options(parser)

        parser.remove_option('--input-path')

    def init(self):
        self.options.input_path = 'temp'
        super().init()

        self.log = init_logger(
            os.path.join(__file__[:-3] + '.log'),
            level=logging.DEBUG if self.options.debug else logging.INFO,
        )

    def zip_dir(self, root_dir, zip_file):
        root_dir = os.path.join(self.options.output_path, self.options.name)
        self.create_temp_dir(root_dir)
        os.chdir(self.options.output_path)
        root_dir = self.options.name
        super().zip_dir(root_dir, zip_file)

    def create_temp_dir(self, root_dir):
        if not self.options.serializers:
            raise Exception('Serializer Invalid args')
        for serializer in self.options.serializers.split(','):
            try:
                serializer_obj = import_module_var(serializer, None)
                model_obj = serializer_obj.Meta.model
                model_name = model_obj.__name__
                json_count = 0
                for obj in model_obj.objects.all():
                    filename = obj.key
                    filename = model_name+filename if filename[0] == '/' else model_name+"/"+filename
                    self.copy_file(dirname=root_dir,
                                   filename=filename, 
                                   data=serializer_obj(obj).data)
                    json_count += 1
                self.log.info("Created files for {} are {}".format(model_name, json_count))
            except Exception as err:
                self.log.error(str(err))

    def copy_file(self, dirname, filename, data, extension=".json"):
        dirpath = os.path.join(dirname, os.path.dirname(filename))
        makedir_p(dirpath)
        json_file = os.path.join(dirname, filename + extension)
        if not os.path.isfile(json_file):
            open(json_file, "w").write(json.dumps(data))

    def close(self):
        close_logger(self.log)

if __name__ == '__main__':
    standalone_main(ItemDataZIP)
