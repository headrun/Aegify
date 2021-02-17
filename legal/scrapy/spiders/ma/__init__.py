import re
from urllib.parse import urljoin
from datetime import datetime
from scrapy.http import Request
from scrapy.selector import Selector
from crawl.scrapy.spiders.base import BaseSpider
from crawl.scrapy.spiders.browse import BasePage, BrowseSpider

SOURCE = 'ma'
SOURCE_URL = 'http://profiles.ehs.state.ma.us/'

def add_url(link):
    url = SOURCE_URL
    return urljoin(url, link)

def clean_data(text):
    clean_txt = ''.join(text).replace('\r\n', '').strip()
    return clean_txt


def person_data(person_info):
    person_name = person_info.split(',')[0]
    try:
        name = person_name.split(' ')
        if len(name) >= 3:
            first_name = name[0]
            last_name = ' '.join(name[2:])
            initial = name[1]
            if re.match("^[a-zA-Z]{1}.$", first_name):
                first_name = ''.join(name[0:-1])
                last_name = name[2]
                initial = ''
            elif not re.match("^[a-zA-Z]{1}.$", initial):
                first_name = name[0]
                last_name = ' '.join(name[1:])
                initial = ''
        else:
            first_name = name[0]
            last_name = ' '.join(name[1:])
        person_data = {'firstName': first_name, 'lastName': last_name, 'middleInitial': initial}
    except:
        initial = ''
        name = person_name.split('.')
        if len(name) > 3:
            first_name = name[0].split(' ')[0]
            initial = name[0].split(' ')[1]
            last_name = ' '.join(name[1:])
        else:
           first_name = name[0]
           last_name = ' '.join(name[1:])
        person_data = {'firstName': first_name, 'lastName': last_name, 'middleInitial': initial}
    return person_data

def get_state_info(state_info):
    state = state_info.strip()[:2]
    zipcode = state_info.replace(state, '').strip()
    return state, zipcode

def businessaddress(address):
    address = ''.join(address).strip().replace('\r\n', ', ')
    city, state, country, zipcode = [''] * 4
    if "No Current Address" in address or  "Buisness Address" in address or "Buisness Address".upper() in address or "RETIRED" in address:
        country = address.split(',')[-1].strip()
        state = address.split(',')[-2].strip()
    elif "None Reported" not in address:
        address_info = address.split(',')
        try:
            add_info = ','.join(address_info[-3:]).strip()
        except:
            add_info = ''
        if re.match('\w+.*,\s?\w{2}\s\d+$', add_info):
            state, zipcode = add_info.split(' ')
            city = address.split(',')[-2]
        elif re.match('\w+.*,\s?\w{2}\s,\s\w+.*', add_info):
            city,state,country = add_info.split(',')
        elif re.match('\w+.*,\s?\w{2}\s\w+\s\w+,\s\w+.*', add_info) or re.match('\w+.*,\s?\w{2}\s\d+.*,\s\w+.*', add_info) or re.match('\w+.*,\s?\w{2}\s\w+.*,\s\w+.*', add_info):
            city,state_info,country = add_info.split(',')
            state = state_info.strip()[:2]
            zipcode =  state_info.replace(state, '').strip()
        elif re.match('\w+,\s\s\d+,\s\w+.*', add_info):
            city, zipcode, country = add_info.split(',')
        elif re.match('\w{2}\s\d+-,\s\w+,\s\w+', add_info):
            add_info = ','.join(address_info[-4:]).strip()
            city =  add_info.split(',')[0]
            state, zipcode = get_state_info(add_info.split(',')[1])
            country = ''.join(add_info.split(',')[-2:]).strip()
        elif len(add_info.split(',')) == 3:
            if add_info.split(',')[0] == '':
                if re.match(',\s\w{2}\s\d+,\s\w+.*', add_info):
                    city, state_info, country = add_info.split(',')
                    state = state_info.strip()[:2]
                    zipcode =  state_info.replace(state, '').strip()
            else:
                city, state_info = add_info.split(',')[1:]
                state = state_info.strip()[:2]
                zipcode =  state_info.replace(state, '').strip()
        if re.findall('\d+', city):
            city = ''
    address_info = [{'address': address, 'city': city.strip(), 'state': state.strip(),
                         'zip_code': zipcode.strip(), 'country': country.strip()}]
    return address_info

def get_date(date):
    date_time = None
    try:
        date_time = str(datetime.strptime(date, '%m/%d/%Y'))
    except:
        date_time = '0000-00-00 00:00:00'
    return date_time

def remove_invalid_date_keys(data):
        for key, value in list(data.items()):
            if not isinstance(value, list):
                if '0000-00-00 00:00:00' in value:
                    del data[key]
        return data

def get_main_data(nodes_xpath, category):
    data_dict = {}
    headers_list = []
    mal_criminals_data = []
    mal_crime_data = []
    for count, mal_crime in enumerate(nodes_xpath):
        if "criminalconvictions" in category:
            mal_headers = ''.join(mal_crime.xpath('.//td//a[contains(@href, "Massachusetts_Criminal_Convictions_Pleas_and_Admissions")]/text()').extract())
        elif "outstatediscipline" in category:
            mal_headers = ''.join(mal_crime.xpath('.//td//a[contains(@href, "Out_of_State_Dicipline")]/text()').extract())
        elif "healthcaredata" in category:
            mal_headers = ''.join(mal_crime.xpath('.//td//a[contains(@href, "Hospital_Discipline")]/text()').extract())
        if 'Charge' in mal_headers: mal_headers = 'charge'
        elif 'Court' in mal_headers: mal_headers = 'court'
        elif 'Jurisdiction' in mal_headers: mal_headers = 'jurisdiction'
        elif mal_headers == 'Plea or Disposition': mal_headers = 'disposition'
        elif 'Plea or Disposition Date' in mal_headers: mal_headers = 'dispositionDate'
        elif 'Docket Number' in mal_headers: mal_headers = 'docketNumber'
        elif 'Conviction' in mal_headers: mal_headers = 'conviction'
        elif 'Sentence' in mal_headers: mal_headers = 'sentence'
        elif mal_headers == 'Facility': mal_headers = 'facility'
        elif 'Facility Type' in mal_headers: mal_headers = 'facilityType'
        elif 'Begin Date' in mal_headers: mal_headers = 'actionBeginDate'
        elif 'End Date' in mal_headers: mal_headers = 'actionEndDate'
        elif 'Basis or Allegation' in mal_headers: mal_headers = 'basisorAllegation'
        elif mal_headers == 'Action': mal_headers = 'action'
        elif 'Date' in mal_headers: mal_headers = 'date'
        elif 'State' in mal_headers: mal_headers = 'state'
        elif 'License Number' in mal_headers: mal_headers = 'selectedstateLicenseNumber'
        elif 'Actions' in mal_headers: mal_headers = 'actions'
        elif 'Action Note' in mal_headers: mal_headers = 'actionNote'
        elif 'Comment' in mal_headers: mal_headers = 'comment'
        mal_rows = ''.join(mal_crime.xpath('.//td[not(contains(text(), "\xa0"))]/text()').extract())
        if not clean_data(mal_rows):
            mal_rows = ' ,'.join(mal_crime.xpath('./td/ul/li/text()').extract())
        if 'date' in mal_headers or 'Date' in mal_headers:
            mal_rows = get_date(mal_rows)
        if mal_headers not in headers_list:
            if mal_headers != '':
                headers_list.append(mal_headers)
                data_dict.update({mal_headers: clean_data(mal_rows)})
        else:
            mal_criminals_data.append(data_dict)
            data_dict = {}
            headers_list = []
            if mal_headers != '':
                headers_list.append(mal_headers)
                data_dict.update({mal_headers: mal_rows})
        if count == len(nodes_xpath)-1:
            mal_criminals_data.append(data_dict)
        mal_crime_data = [ele for ele in ({key: val for key, val in sub.items() if val and '0000-00-00 00:00:00' not in val} for sub in mal_criminals_data) if ele]
    return mal_crime_data

#xpaths for ma_terminal
person_xpath = '//div[@class="col-sm-12 name"]/text()'
licence_xpath = '//div[@class="col-sm-5 col-md-4 col-lg-5"]//a[contains(text(), "{}")]//..//following-sibling::div[1]//text()'
licence_sub_xpath = '//div[@class="col-sm-4 col-md-3 col-lg-2"]//a[contains(text(), "{}")]//..//following-sibling::div[1]/text()'
div_post_xpath = '//div[@class="col-sm-4 col-md-3 col-lg-2"]//a[contains(text(), "{}")]//..//following-sibling::div//ul/li/text()'
div_award_xpath = '//div[@class="col-md-12"]//div//a[contains(text(), "{}")]//..//..//following-sibling::div//ul/li//text()'
health_care_xpath = '//div[@class="row section discipline"]//div[contains(@class,"col-md-12")]//table[@class="hosp_disc"]//td//a[contains(text(), "{}")]//..//following-sibling::td//text()'
health_xpath = '//div[@class="row section discipline"]//div[contains(@class,"col-md-12")]//table[@class="hosp_disc"]//td'
board_xpath = './/div[@class="col-sm-4 col-md-3 col-lg-2"]//a[contains(text(), "{}")]//..//following-sibling::div[1]//text()'
abms_xpath = '//div[@class="col-sm-12"]//a[contains(text(),"ABMS")]//text()'
aoa_xpath = '//div[@class="col-sm-12"]//a[contains(text(),"AOA")]//text()'
malpractice_claims_xpath = '//div[@class="row section malpractice"]//div//a[contains(text(), "Massachusetts Malpractice Claims")]//..//..//table//tr[position()>1]'
malpractice_specialist = '//div[@class="details"]//a[contains(text(), "Details for Payments")]/text()'
board_displine_xpath = '//div[@class="col-md-12 discipline_detail"]//div[@class="row"]'
mal_crime_xpath = '//a//text()[contains(.,"Massachusetts Criminal Convictions, Pleas and Admissions")][not(contains(., "Out of State Board Discipline"))]//..//..//..//following-sibling::div//table[not(contains(@class,"hosp_disc"))]//tbody//tr'
out_board_xpath = '//a//text()[contains(.,"Out of State Board Discipline")]//..//..//following-sibling::div[not(contains(@class, "col-md-12 discipline_detail"))]//table//tr'
hospital_xpath = '//a//text()[contains(.,"Health Care Facility Discipline")]//..//..//..//following-sibling::div//table//tr'
