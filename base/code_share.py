import os, sys
sys.path.insert(1, os.getcwd())
import shutil
import logging
import importlib

from datetime import datetime, timedelta
from optparse import OptionParser

from base.settings import DjangoUtil;
settings = DjangoUtil.settings()
from base.utils import standalone_main, init_logger, close_logger, makedir_p

def get_timestamp():
    timestamp = datetime.now().strftime('%d-%m-%Y_%H_%M_%S')
    return timestamp

class ProjectCodeShare(object):
    def _init_site(self):
        self.site_name = os.environ.get('SITE', None)
        self.tar_file_name = "Tracking-{}-{}".format(self.site_name,\
            str(int(datetime.utcnow().timestamp())))

    def parse(self):
        parser = OptionParser()

        parser.add_option("", "--code-share", dest="site_code_share", action="store_true",\
            default=False, help="To share the code to customer")
        parser.add_option("", "--pyc", dest="pyc_dir", action="store_true",\
            default=False, help="To remove __pycache__ dirs")
        parser.add_option("-c", "--code-share-dirs", dest="code_share_dirs",\
            default=[], help="To share provided dirs")

        (self.options, args) = parser.parse_args()
        self.log = init_logger(os.path.join(__file__[:-3] + '.log'),level=logging.INFO,)

    def process(self):
        code_share_dirs=self.get_code_share_dirs()
        if code_share_dirs.get('error',None):
            return code_share
        try:
            complile_dirs   = " ".join([_app for _app in code_share_dirs.get('success', ['.'])])
            compile_cmd     = "python3 -m compileall {} deploy manage.py scrapy.cfg sites/__init__.py ".format(complile_dirs)
            os.system(compile_cmd)
            compile_out_file="{}_complied_pyc_files".format(self.site_name)
            compile_pyc_cmd = "find {} -name '*.pyc' > {} ".format(
                complile_dirs,
                compile_out_file)
            os.system(compile_pyc_cmd)
            self.log.info("Complied dirs are {} ".format(compile_pyc_cmd))
            self.generate_zip_file(compile_out_file, complile_dirs)
        except Exception as e:
            self.log.info(" Failed to create the zip file ", str(e))

    def init_dirs(self, dirs, site_pyc_dir):
        for _dir in dirs:
            dir_path = os.path.join(site_pyc_dir, _dir)
            dir_name = os.path.dirname(dir_path)
            if not os.path.isdir(dir_name):
                makedir_p(dir_name)

    def copy_file(self, files, site_dir):
        for src, des in files.items():
            shutil.move(src, os.path.join(site_dir, des))

    def generate_zip_file(self, outfile, dirs):
        site_pyc_dir = self.tar_file_name
        if not os.path.isdir(site_pyc_dir):
            makedir_p(site_pyc_dir)

        with open(outfile,'r') as f:
            data = f.read()

        if self.options.pyc_dir:
            dirs = list(set(d.replace("__pycache__/", "") for d in data.split()))
            data = { d:d.replace("__pycache__/", "") for d in data.split()}
        else:
            dirs = list(set(d for d in data.split()))
            data = {f:f for f in data.split()}

        self.init_dirs(dirs, site_pyc_dir)
        self.copy_file(data, site_pyc_dir)

        tar_file_name = "{}.tgz".format(self.tar_file_name)
        os.system("tar -cvzf {} {}".format(tar_file_name, site_pyc_dir))
        shutil.move(os.path.join(tar_file_name), os.path.join(settings.MEDIA_ROOT, tar_file_name))
        remove_complied_files = "{} {} ".format(site_pyc_dir, outfile)
        self.log.info(" Removed Things are {}".format(remove_complied_files))
        os.system( "rm -rf {}".format(remove_complied_files))

    def get_code_share_dirs(self):
        self._init_site()
        if self.options.code_share_dirs:
            return {
                "success": self.options.code_share_dirs.split(',')
            }
        if not self.site_name:
            return {
                "error":"SITE=<$SITE> is not present in sites."
            }
        site_module="sites.{}".format(self.site_name)
        obj = importlib.import_module(site_module)
        return {
            "success": obj.DEPLOY_DIRS
        }

    def close(self):
        close_logger(self.log)  

if __name__ == '__main__':
    standalone_main(ProjectCodeShare)
