from urllib.parse import urlparse
from urllib.parse import urlencode
import json
from . import *

class MainPage(BasePage):
    def request(self):
        params = (
            ('custom', 'sorting:relevance,se:salons'),
            ('q', 'salons'),
        )
        self.pageIndex = getattr(self, 'pageIndex', 1)
        self.url = 'https://www.purplle.com/bookings/filter/ajax/gurgaon/%s?'%self.pageIndex + urlencode(params)
        return Request(self.url, meta = {'pageCount':self.pageIndex})

    def parse(self, response):
        pageCount = response.meta['pageCount']
        data_ = json.loads(response.text)
        pages = data_.get('pages','')
        datas = data_.get('list',[])
        for data in datas:
            name = data.get('name','')
            href = data.get('slug','')
            salon_class = data.get('class','')
            category = data.get('type_name','')
            location = data.get('area_name','')
            ratings = data.get('user_rating',{}).get('ratings','')
            rating_count = data.get('user_rating',{}).get('avg_rating','')
            city = 'gurgaon'
            main_page_details = {'salonName':name, 'salonClass':salon_class, 'storeCategory':category, 'localityName':location, 'rating':ratings, 'ratingCount':rating_count, 'city':city}
            data = {'name': 'basic_details', 'basic_details': main_page_details}
            url = 'https://www.purplle.com/bookings/gurgaon/%s-v'%href
            yield self.spider.get_item(self, SOURCE, href, data, None, url=url, field_name='listing')

        if datas:
            pageCount = pageCount+1
            url = 'https://www.purplle.com/bookings/filter/ajax/gurgaon/%s?'%pageCount
            yield MainPage(self, url=url, pageIndex=pageCount)

class MySpider(BrowseSpider):
    name = SOURCE + '_browse'
    source_name = SOURCE

    MODEL = 'Browse'

    main_page_class = MainPage
