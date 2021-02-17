import os

os.environ['APP_LIST'] = str([
                            'crawl',
                            'legal',
                        ])

from base.settings.django import *

API_APP_LIST = [
                'legal',
            ]
