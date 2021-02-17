from django.conf import settings
from yaml import load
import os
from base.utils import import_module_var


class Configure:
    '''
    Setup appropriate Environment Variables and load change the database 
    settings based on site attribute
    parameters:
        site: string
    '''

    def __init__(self, site, *args, **kwargs):
        with open('base/settings/environ.yaml', 'r') as file:
            configs = load(file)
            for key, val in configs[site].items():
                os.environ[key] = val
        self._change_db()

    def _change_db(self):
        PROJECT = os.environ.get(
            'ENV_PROJECT', os.path.basename(settings.BASE_DIR))
        settings.DATABASES['default']['NAME'] = os.environ.get(
            'MYSQL_DATABASE', PROJECT + '_' + os.environ['SITE'])

        settings.DATABASES['default']['USER'] = os.environ.get(
            'MYSQL_USER', 'root')

        settings.DATABASES['default']['PASSWORD'] = os.environ.get(
            'MYSQL_PASSWORD', '')

        settings.DATABASES['default']['HOST'] = os.environ.get(
            'MYSQL_HOST', 'localhost')

        settings.DATABASES['default']['PORT'] = os.environ.get(
            'MYSQL_PORT', '')
