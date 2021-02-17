from urllib.parse import urljoin, urlencode

from scrapy.http import Request, FormRequest
from scrapy.selector import Selector

from crawl.scrapy.validators import OKSchemaItem
from crawl.scrapy.spiders.base import BaseSpider
from crawl.scrapy.spiders.browse import BasePage, BrowseSpider

import requests
import json
from time import sleep
import re

SOURCE = 'georgia'
SOURCE_URL = 'https://gcmb.mylicense.com/verification/'
USERNAME = 'Innominds'
PASSWORD = 'Helloworld1234'

def upload_sitekey(url, site_key):
    token = {"proxytype": "HTTP", "pageurl": url, "googlekey": site_key}
    files = {
    'username': (None, USERNAME),
    'password': (None, PASSWORD),
    'type': (None, '4'),
    'token_params': (None, json.dumps(token)),
        }
    response = requests.post('http://api.dbcapi.me/api/captcha', files=files)
    result = parse_response(response.text)
    return result
def parse_response(response_body):
    try:
        response_dic = dict([e.split('=', 1) for e in response_body.split('&')])
        return response_dic
    except:
        return {}
def get_recaptcharesult(captcha_id):
    count = 25
    while count >= 0:
        sleep(10)
        if captcha_id:
            r = requests.get('http://api.dbcapi.me/api/captcha/{0}'.format(captcha_id))
            result = parse_response(r.text)
            if result.get('text'):
                return result
        count = count - 1
    return {}
def report_captcha(captcha_id):
	files = {
        'username': (None, USERNAME),#jatinv'),
        'password': (None, PASSWORD),#p@ss4DBC'),
	}
	url  = 'http://api.dbcapi.me/api/captcha/{0}/report'.format(captcha_id)
	response = requests.post(url, files=files)
	print("your captcha has been reported.")

def get_googlecaptcha(url, site_key):
    upload_details = upload_sitekey(url, site_key)
    result = get_recaptcharesult(upload_details.get('captcha'))
    report_captcha(upload_details.get('captcha'))
    print(upload_details)
    print(result)
    if result.get('text'):
        return result.get('text')
    else:
        return ''
def personNameFormat(name):
    first_name, middle_name, last_name, suffix = ['']*4
    name_list = re.findall('(.+?)(?:,|$)', name)
    if len(name_list) >= 3:
        last_name, first_name, suffix = name_list[:3]
    elif len(name_list) == 2:
        last_name, first_name = name_list
    elif len(name_list) == 1:
        first_name = name
    middle_name_format = re.findall('\w+\.?\w*', first_name)
    if middle_name_format:
        try:
            first_name = middle_name_format[0]
            middle_name = ' '.join(middle_name_format[1:])
        except:
            first_name = ' '.join(middle_name_format)
    formatted_name = {
        'firstName':first_name.strip(),
        'middleName': middle_name.strip(),
        'lastName': last_name.strip(),
        'suffix': suffix.strip('. '),
        'personFullName': name
    }
    return formatted_name

