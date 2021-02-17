import requests
import json
from time import sleep
import re
def upload_sitekey(url, site_key):
    token = {"proxytype": "HTTP", "pageurl": url, "googlekey": site_key}
    files = {
    'username': (None, 'Innominds'),
    'password': (None, 'Helloworld1234'),
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
    # import pdb;pdb.set_trace()
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
    	'username': (None, 'Innominds'),#jatinv'),
    	'password': (None, 'Helloworld1234'),#p@ss4DBC'),
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