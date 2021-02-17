from urllib.parse import urljoin, urlencode

from scrapy.http import Request, FormRequest
from scrapy.selector import Selector

from crawl.scrapy.validators import OKSchemaItem
from crawl.scrapy.spiders.base import BaseSpider
from crawl.scrapy.spiders.browse import BasePage, BrowseSpider
from datetime import datetime
from dateutil.parser import parse
import re

SOURCE = 'dea'
SOURCE_URL = 'https://www.deadiversion.usdoj.gov/'

def personNameFormat( person_name):
    first_name, middle_name, last_name = [''] * 3
    doc_names = re.findall('\w+\.?\w*', person_name)
    if len(doc_names) >= 3:
        first_name, middle_name, last_name = doc_names[:3]
    elif len(doc_names) == 2:
        first_name, last_name = doc_names
    else:
        first_name = ''.join(doc_names)
    return (first_name, middle_name, last_name)

def details( name, date, file_year):
    main_page_details = {}
    business_type_list = ['LLC', 'Inc.','Wholesale', 'Enterprises', 'Distribute', 'Shop', 'Network', 'Business', 'Trading', 'Apothecary','Pharmacy & Surgical', 'International', 'Whosale', 'Co.', 'Construction', 'Associates', 'Drug', 'Pharmac', 'Clinic', 'Café', 'Diagnostic', 'Medicine', 'Tree', 'Market', 'L.L.C', 'Distribut', 'Innovations', 'Detectives', ' Group', 'Corporation', 'corporated', 'Corp.', ' Foods', ' Health Services', 'Sales', 'Shelter', 'Farmacia']
    business_type_re = ['\w+\.\w{2,3}', '\w+\'s\s\w+']
    person_type_acronym = ['RN', 'DO', 'DDS', 'DPM', 'ARNP', 'DVM', 'APRN', 'MD', 'FNP', 'RN/APN', 'PhD', 'NP', 'APN', 'PA', 'DMD']
    case_type_list = ["Revocation of Practitioner's Registration, Denial of Application for Exporter's Registration", 'Denial of Application for Fees and Expenses Under the Equal Access to Justice Act', 'Revocation of Registration, Denial of Request for Change of Registered Location', 'Order Regarding Officially Noticed Evidence and Motion for Reconsideration', 'Order Rescinding Final Order Denying Application for Registration', 'Revocation of Registration and Denial of Application - Correction', 'Order Accepting Settlement Agreement and Terminating Proceeding', 'Denial of Request for Registration To Handle List I Chemicals', 'Denial of Request for Registration to Handle List I Chemicals', 'Declaratory Order Terminating Exemption From Registration', 'Grant of Renewal Application and Dismissal of Proceeding', 'Denial of Application for Change of Registered Address', 'Revocation of Registration and Denial of Application', 'Granting of Renewal Application Subject to Condition', 'Grant Registration to Import Schedule II Substances', 'Affirmance of Immediate Suspension of Registration', 'Denial of Request for Modification of Registration', 'Continuation of Registration with Restrictions', 'Continuation of Registration With Restrictions', 'Notice of Withdrawal of Denial of Application', 'Declaratory Order Terminating Registrations', 'Denial of Application for DEA Registration', 'Declaratory Order Terminating Registration', 'Affirmance of Immediate Suspension Order', 'Denial of Application for Registration', 'Revocation and Denial of Registration', 'Order Dismissing Order To Show Cause', 'Introduction and Procedural History', 'Affirmance of Immediate Suspension', 'Denial of Application (Correction)', 'Denial of Application- Correction', 'Grant of Conditional Registration', 'Denial of Request for Redactions', 'Grant of Restricted Registration', 'Decision and Order - Correction', 'Order Denying Procurement Quota', 'Affirmance of Suspension Orders', 'Affirmance of Suspension Order', 'Order Terminating Registration', 'Denial of Request for Hearing', 'Continuation of Registration', 'Revocation of Registrations', 'Suspension of Registration', 'Revocation of Registration', 'Denial of Motion for Stay', 'Admonition of Registrant', 'Change in Effective Date', 'Dismissal of Proceedings', 'Suspension Registration', 'Suspension of Shipments', 'Dismissal of Proceeding', 'Denial of Applications', 'Denial of Registration', 'Denial of Application', 'Denial Of Application', 'Orders to Show Cause', 'Grant of Application', 'Decision and Orders', 'Decision And Order', 'Procedural History', 'Decision and Order', 'Declaratory Order', 'Notice of Hearing', 'Order']
    formated_name, case_type = '', ''
    person_check, business_check = False, False
    person_name_re, degree_types = [], []
    if ';' in name:
        doctor_details_list = name.split(';')
        business_details_list = name.split(';')
        if len(doctor_details_list) == 3 and doctor_details_list[1].strip() in case_type_list:
            formated_name = doctor_details_list[0]
            case_type = '; '.join(doctor_details_list[1:]).strip()
        elif business_details_list[0].split('.')[-1].strip() in case_type_list:
            for each_case in case_type_list:
                business_name = name.split(';')[0]
                if each_case in business_name:
                    formated_name = business_name.replace(each_case, '').strip()
                    case_type = name.split(';')[-1].strip()
                    break
        else:
            formated_name, case_type = name.rsplit(';', 1)
            # doctor_details_list = name.split(';')[:-1]
    elif ':' in name:
        formated_name, case_type = name.rsplit(':', 1)
        # doctor_details_list = name.split(';')[:-1]
    else:
        for each_case in case_type_list:
            if each_case in name:
                case_type = each_case
                formated_name = name.replace(each_case, '').strip()
                break
    if ' by ' in formated_name:
        # To handled special case in person name
        formated_name = formated_name.split(' by ')[-1]
    if ' Matter of ' in formated_name:
        # To handled special case in person name "In the Matter of James Jay Rodriguez, M.D."
        formated_name = formated_name.split(' Matter of ')[-1]
    if formated_name in case_type_list:
        #To handle these case: "Decision and Order: Zelideh I. Cordova-Velazco, M.D."
        formated_name, case_type = (case_type.strip(), formated_name)

    designation_check_re = re.findall(',\s+[A-Za-z.]{1,7}\.?', formated_name) or\
                           re.findall('^\w+\s\w\.\s\w+(,\s+[A-Za-z]{2,3})$', formated_name)
    if designation_check_re:
        #case 1
        for designation_check in designation_check_re:
            if designation_check.replace('.','').strip(' ,') in person_type_acronym:
                person_check = True
                person_re = designation_check
                degree_types.append(designation_check.replace('.','').strip(' ,'))
            elif designation_check.strip('. ,') in business_type_list:
                business_check = True
    else:
        person_name_re = re.findall('\w+\s\w\.\s\w+$', formated_name) or \
                        re.findall('\w+\s\w\.\s\w+,\s[JSr]{2}\.?', formated_name)
        if person_name_re:
            person_check = True

    if not person_check and not business_check:
        person_name_re = re.findall('\w+\s\w\.\s\w+$', formated_name) or \
                        re.findall('\w+\s\w\.\s\w+,\s[JSr]{2}\.?', formated_name)
        if person_name_re:
            person_check = True
        elif not person_name_re:
            business_check = any(ele in formated_name for ele in business_type_list) or \
                        any(re.match(ele, formated_name) for ele in business_type_re)
    if person_check and not business_check:
        first_name, middle_name, last_name = [''] * 3
        person_name_re = person_name_re or re.findall('(\w+.*)%s'%person_re, formated_name)
        if person_name_re:
            person_name = person_name_re[0]
            first_name, middle_name, last_name = personNameFormat(person_name)
            main_page_details.update({'firstName': first_name.strip(), 'middleInitial': middle_name.strip(), 'lastName': last_name.strip(), 'personName': person_name, 'doctorType': ', '.join(degree_types)})
        else:
            pass
    elif business_check and not person_check:
        main_page_details['businessName'] = formated_name
    elif business_check and person_check:
        #TODO
        pass
    else:
        main_page_details['title'] = formated_name
    main_page_details['typeOfCase'] = case_type.strip()
    try:
        main_page_details['casePostDate'] = str(datetime.strptime(date, '%B %d, %Y').date())
    except:
        try:
            main_page_details['casePostDate'] = str(parse(date))
        except:
            pass
    if file_year:
        main_page_details.update({'dataFileYear': file_year})
    return main_page_details

