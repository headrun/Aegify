from ..media import *

class TestSpider(MediaSpider):
    name = source_name = 'media'
    MODEL = 'ImageModel'

    main_page_class = MediaPage
