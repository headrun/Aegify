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
import os
from datetime import datetime
from collections import OrderedDict

SOURCE = 'georgia'
SOURCE_URL = 'https://gcmb.mylicense.com/verification/'
USERNAME = os.environ.get('USERNAME', None)
PASSWORD = os.environ.get('PASSWORD', None)

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
    if suffix.strip('. ').isdigit():
        formatted_name['suffix'] = ''
    return formatted_name

def get_graduation_info(education_info, search_key, data_key):
    graduated_date, university_name, country = None, [], None
    for education in education_info:
        try:
            current_graduated_date = datetime.strptime(education.get(search_key, ''), '%Y-%m-%d %H:%M:%S')
            if graduated_date and current_graduated_date > graduated_date:
                graduated_date = current_graduated_date
                university_name = [education.get(data_key, '')]
                country = education.get('country', '')
            elif graduated_date and current_graduated_date == graduated_date:
                university_name.append(education.get(data_key, ''))
                country = education.get('country', '')
            elif not graduated_date:
                graduated_date = current_graduated_date
                university_name = [education.get(data_key, '')]
                country = education.get('country', '')
        except:
            pass
    return (graduated_date, university_name, country)

def generate_graduation_info(education_data):
    education_graduated_date, graduated_date = None, None
    education_info = education_data.get('educationInfo', [])
    graduate_medical_info = education_data.get('medicalEducationInfo', [])
    if education_info:
        education_graduated_date, education_university_name, country = get_graduation_info(education_info, 'graduated', 'schoolName')
        if not education_graduated_date:
            education_graduated_date, education_university_name, country = get_graduation_info(education_info, 'toDate', 'schoolName')
    if graduate_medical_info:
        graduated_date, graduate_university_name, country = get_graduation_info(graduate_medical_info, 'graduated', 'hospitalName')
        if not graduated_date:
            graduated_date, graduate_university_name, country = get_graduation_info(graduate_medical_info, 'toDate', 'hospitalName')
    graduated_year, university_name, graduated_country = '', '', ''
    if education_graduated_date and graduated_date:
        if education_graduated_date == graduated_date:
            graduated_year = education_graduated_date.year
            university_name = education_university_name
            graduated_country = country
        elif education_graduated_date < graduated_date:
            graduated_year = graduated_date.year
            university_name = graduate_university_name
            graduated_country = country
        elif education_graduated_date > graduated_date:
            graduated_year = education_graduated_date.year
            university_name = education_university_name
            graduated_country = country
    elif education_graduated_date and not graduated_date:
        graduated_year = education_graduated_date.year
        university_name = education_university_name
        graduated_country = country
    elif graduated_date and not education_graduated_date:
        graduated_year = graduated_date.year
        university_name = graduate_university_name
        graduated_country = country
    education_data["additionalInfo"]["educationInfo"] = education_data.get('educationInfo', '')
    education_data["additionalInfo"]["medicalEducationInfo"] = education_data.get('medicalEducationInfo', '')
    education_data.pop('educationInfo')
    education_data.pop('medicalEducationInfo')
    education_data['graduationYearfromCollege'] = graduated_year
    if university_name or graduated_country:
        education_data['universityInfo'] = {'universityName': university_name, 'country': graduated_country}
    else:
        education_data['universityInfo'] = {}
    return education_data

def generate_primary_speciality(data):
    speciality_list = data.get('primarySpecialty', [])
    data.pop('primarySpecialty')
    primary_speciality_count = 1
    sub_speciality_count = 1
    for each_speciality in speciality_list:
        if each_speciality.get('specialty', '') or each_speciality.get('certifyingBoard', ''):
            if each_speciality.get('isPrimarySpecialty') == 'Y':
                if primary_speciality_count > 1:
                    key = "primarySpecialty_" + str(primary_speciality_count)
                    certified_key = 'PS ' + str(primary_speciality_count) + ' certifyingBoard'
                else:
                    key = "primarySpecialty"
                    certified_key = 'PS certifyingBoard'
                data[key] = each_speciality.get('specialty', '')
                data[certified_key] = each_speciality.get('certifyingBoard', '')
                primary_speciality_count +=1
            if each_speciality.get('isPrimarySpecialty') == 'N':
                certified_key = 'SS '+ str(sub_speciality_count) + ' certifyingBoard'
                key = "subSpecialty_" + str(sub_speciality_count)
                data[key] = each_speciality.get('specialty', '')
                data[certified_key] = each_speciality.get('certifyingBoard', '')
                sub_speciality_count +=1
    return data



def find_valid_suffix_from_name(name, suffix_list, suffix_name, type_of_name):
    data = {}
    valid_list = [ele for ele in suffix_list if ele == name]
    if valid_list:
        if type_of_name == "firstMiddle":
            middle_name_format = re.findall('\w+\.?\w*', suffix_name)
            if middle_name_format:
                try:
                    data["firstName"] = middle_name_format[0].strip()
                    data["middleName"] = ' '.join(middle_name_format[1:]).strip()
                except:
                    data["firstName"] = ' '.join(middle_name_format).strip()
            data["suffix"] = name
        elif type_of_name == "lastName":
            data["suffix"], data["lastName"] = (name, suffix_name)
        elif type_of_name == "middleName":
            data["suffix"], data["middleName"] = (name, suffix_name)
        return (valid_list, data)
    else:
        valid_list = [ele for ele in name.split() if ele.replace('.', '').replace(' ', '').strip() in suffix_list]
        if valid_list:
            data["suffix"] = valid_list[0]
            if type_of_name == "firstMiddle":
                data["firstName"] = name.replace(valid_list[0], '')
            elif type_of_name == "middleName":
                data["middleName"] = name.replace(valid_list[0], '')
            elif type_of_name == "lastName":
                data["lastName"] = name.replace(valid_list[0], '')
        return (valid_list, data)

def suffixFormation(data):
    suffix_list = ['Jr', 'JR', 'jr', 'SR', 'Sr', 'sr', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX', 'IIl', 'lll']
    designation = ['MD', 'MBBS', 'DO', 'CAA', 'PA-C', 'DMSC', 'MS', 'Ms', 'D.O', 'PHD', 'DPM', 'NP', 'RN/APN', 'FNP, RN', 'PA', 'APN', 'DDS', 'DVM', 'ARNP', 'APRN', 'DMD', 'DO', 'DR', 'DR', 'DMS']
    #verifying suffix present in the firstName, lastName, middleName
    valid_suffix_list, result_data = find_valid_suffix_from_name(data.get('personName', {}).get('firstName', ''), suffix_list, data.get('personName', {}).get('suffix', ''), "firstMiddle")
    if valid_suffix_list:
        data["personName"].update(result_data)
    valid_suffix_list, result_data = find_valid_suffix_from_name(data.get('middleName', {}).get('middleName', ''), suffix_list, data.get('personName', {}).get('suffix', ''), "middleName")
    if valid_suffix_list:
        data["personName"].update(result_data)
    valid_suffix_list, result_data = find_valid_suffix_from_name(data.get('personName', {}).get('lastName', ''), suffix_list, data.get('personName', {}).get('suffix', ''), "lastName")
    if valid_suffix_list:
        data["personName"].update(result_data)
    #designation in suffix
    suffix = data.get('personName', {}).get('suffix', '').replace('.', '').replace(' ', '')
    if suffix and suffix not in suffix_list:
        if suffix and suffix.upper() in designation:
            if not data.get('designation', ''):
                data["designation"] = data.get('personName', {}).get('suffix', '').upper()
        data["personName"]["suffix"] = ""
    return data

def generate_final_output(data):
    final_dict = OrderedDict()
    keys_list = ['personName', 'licenseType', 'designation', 'status', 'licenseNumber', 'profession', 'professionSubtype', 'licenseIssueDate', 'licenseExpiryDate', 'licenseRenewalDate', 'Specialty', 'certifyingBoard', 'streetAddress', 'state', 'zipCode', 'county', 'country', 'relatedLicenses', 'publicDocuments', 'profileSubmissionDate', 'initialLicensureState', 'initialLicenseIssueDate', 'malpracticeCoverage', 'currentPracticeLocation', 'acceptingMedicaidPatients', 'acceptingMedicarePatients', 'graduationYearfromCollege', 'universityInfo', 'currentHospitalPrivileges', 'disciplinaryAction', 'privilegeRevocations', 'criminalOffensesStatus', 'arbitrationAwards', 'settlementAmounts', 'membershipInOrganizations', 'awards', 'medicalSchoolFaculties', 'firstRecordScrapeDate', 'lastRecordScrapeDate', 'lastRecordDataStatus', 'additionalInfo']
    customized_keys = ['currentHospitalPrivileges', 'disciplinaryAction', 'privilegeRevocations', 'criminalOffensesStatus', 'arbitrationAwards', 'settlementAmounts']
    for each_key in keys_list:
        if each_key in customized_keys:
            index = 1
            if data.get(each_key, []):
                for each_record in data.get(each_key, []):
                    for (key,value) in each_record.items():
                        dict_key = each_key + '_' + str(index) + '.' + key
                        final_dict[dict_key] = value
                    index = index + 1
                    if index > 6:
                        break
            else:
                final_dict[each_key] = data.get(each_key, [])
        else:
            valid = False
            for key in data.keys():
                if each_key in key:
                    valid = True
                    final_dict[key] = data[key]
            if not valid:
                if 'Specialty' not in each_key and 'certifyingBoard' not in each_key:
                    final_dict[each_key] = data.get(each_key, '')
    final_dict = suffixFormation(final_dict)
    return final_dict

def key_encryption(key_data):
    data = [ele for ele in key_data.replace(',', '').replace('-', '').replace('_', '').strip().split(' ') if ele]
    return '-'.join(data)

def key_decryption(key_data):
    data = [ele for ele in key_data.replace(',', '').replace('-', '').replace('_', '').strip().split(' ') if ele]
    return ' '.join(data)

def generate_unique_key(keys_list):
    unique_list = []
    for each_key in keys_list:
        unique_list.append(key_encryption(each_key))
    unique_key = '_'.join(unique_list)
    return unique_key

def data_from_unique_key(unique_key):
    data = {}
    keys = ['licenseType', 'licenseNumber', 'status', 'personName', 'address']
    unique_key_list = unique_key.split('_')
    for (key, value) in zip(keys, unique_key_list):
        data[key] = ' '.join(value.split('-')).strip()
    return data