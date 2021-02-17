from . import *

class MainPage(BasePage):
    def request(self):
        if not self.url:
            self.url = 'http://profiles.ehs.state.ma.us/ProfilesV3/Physician?Search=full&State=%s' %(self.key)
        return Request(self.url)

    def parse(self, response):
        sel = Selector(response)
        nodes = sel.xpath('//table[@class="SearchResults"]//tr[@class="tabular"]')
        for node in nodes:
            physician_link = clean_data(node.xpath('.//td//a[contains(@href, "ProfilesV3/Physician")]/@href').extract())
            url = add_url(physician_link)
            first_name = clean_data(node.xpath('.//td[2]/text()').extract())
            last_name = clean_data(node.xpath('.//td//a/text()').extract())
            intial = clean_data(node.xpath('.//td[3]/text()').extract())
            practice_spec = clean_data(node.xpath('.//td[4]/text()').extract())
            license_status = clean_data(node.xpath('.//td[5]/text()').extract())
            town_city = clean_data(node.xpath('.//td[6]/text()').extract())
            state = clean_data(node.xpath('.//td[7]/text()').extract())
            main_page_data = {'firstName': first_name, 'lastName': last_name,
                              'middleInitial': intial, 'practice_spec': practice_spec,
                              'license_status': license_status,
                              'town_city': town_city, 'state': state
                             }
            data = {'name': 'basic_details', 'basic_details': main_page_data}
            yield self.spider.get_item(self, SOURCE, physician_link, data, url=url, field_name='listing')


        page = sel.xpath('//button[@name="SetPage"][contains(text(),"Next")]/@value').extract_first()
        url = "http://profiles.ehs.state.ma.us/ProfilesV3/Physician?Search=full&State=%s&Page=" %(self.key) + str(page)
        yield MainPage(self, url=url)

class MySpider(BrowseSpider):
    name = SOURCE + '_browse'
    source_name = SOURCE
    MODEL = 'Browse'
    main_page_class = MainPage
