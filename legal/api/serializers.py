from datetime import datetime
from dateutil.parser import parse
from django.db.models import Max

import re
from datetime import datetime, timedelta
from crawl.api.serializers import *
from ..scrapy.spiders.georgia import generate_graduation_info, generate_primary_speciality, generate_final_output, suffixFormation

from ..models import *

class SourceSerializer(BaseSourceSerializer):
    class Meta(BaseSourceSerializer.Meta):
        model = Source
        fields = ['name', 'url']

class ListingTerminalItemKeySerializer(BaseItemKeySerializer):
    source = SourceSerializer()

    class Meta(BaseItemKeySerializer.Meta):
        model = ListingTerminal

class DetailTerminalItemKeySerializer(BaseItemKeySerializer):
    source = SourceSerializer()

    class Meta(BaseItemKeySerializer.Meta):
        model = DetailTerminal

class BrowseListCreateSerializer(BaseItemListCreateSerializer):
    source = SourceSerializer()

    class Meta(BaseItemListCreateSerializer.Meta):
        model = Browse

class BrowseDetailSerializer(BaseItemDetailSerializer):
    source = SourceSerializer()

    items = ListingTerminalItemKeySerializer(many=True)

    class Meta(BaseItemDetailSerializer.Meta):
        model = Browse
        fields = ['source', 'key', 'url', 'active', 'items']

class ListingTerminalListCreateSerializer(BaseItemListCreateSerializer):
    source = SourceSerializer()

    class Meta(BaseItemListCreateSerializer.Meta):
        model = ListingTerminal

class ListingTerminalDetailSerializer(BaseItemDetailSerializer):
    source = SourceSerializer()

    def get_data(self, obj):
        data, person_details = {}, {}
        for d in self.get_data_list(obj):
            da = d.json
            details = da.get('basic_details', {})
            if details:
                person_details.update(details)
            if d.name == 'massachusetts_meta':
                da['personName'] = {'firstName': person_details.get('firstName'),
                                   'lastName':  person_details.get('lastName'),
                                   'middleInitial' : person_details.get('middleInitial')}
                if data.get('basic_details'):
                    data.pop('basic_details')
                data.update(da)
                group_keys = ['businessAddress', 'outofstateDiscipline', 'boardCertifications', 'healthcarefacilityDiscipline', 'boarddiscipline', 'criminalConvictions', 'malpracticeclaims']
                for i, group_key in enumerate(group_keys):
                    for each in da.get(group_key, []):
                        if 'groups' in each.keys():
                            group = each.pop('groups',None)

            elif d.name is '':
                data.update(da)
            else:
                data.setdefault(d.name, []).append(da)
        return data

    class Meta(BaseItemDetailSerializer.Meta):
        model = ListingTerminal
        fields = ['source', 'key', 'url', 'active', 'data']

    def get_courses(self, obj):
        return [DetailTerminalItemKeySerializer(x).data for x in obj.course_browse.items.all()] if obj.course_browse else []


class DetailTerminalListCreateSerializer(BaseItemListCreateSerializer):
    source = SourceSerializer()

    class Meta(BaseItemListCreateSerializer.Meta):
        model = DetailTerminal



class DetailTerminalDetailSerializer(BaseItemDetailSerializer):
    source = SourceSerializer()

    def personNameFormat(self, person_name):
        first_name, middle_name, last_name = [''] * 3
        doc_names = re.findall('\w+\.?\w*', person_name)
        if len(doc_names) >= 3:
            first_name, middle_name, last_name = doc_names[:3]
        elif len(doc_names) == 2:
            first_name, last_name = doc_names
        else:
            first_name = ''.join(doc_names)
        return (first_name, middle_name, last_name)

    def details(self, name, date, file_year):
        main_page_details = {}
        business_type_list = ['LLC', 'Inc.','Wholesale', 'Enterprises', 'Distribute', 'Shop', 'Network', 'Business', 'Trading', 'Apothecary','Pharmacy & Surgical', 'International', 'Whosale', 'Co.', 'Construction', 'Associates', 'Drug', 'Pharmac', 'Clinic', 'Café', 'Diagnostic', 'Medicine', 'Tree', 'Market', 'L.L.C', 'Distribut', 'Innovations', 'Detectives', ' Group', 'Corporation', 'corporated', 'Corp.', ' Foods', ' Health Services', 'Sales', 'Shelter', 'Farmacia', ' Pills']
        business_type_re = ['\w+\.\w{2,3}', '\w+\'s\s\w+']
        person_type_acronym = ['RN', 'DO', 'DDS', 'DPM', 'ARNP', 'DVM', 'APRN', 'MD', 'FNP', 'RN/APN', 'PhD', 'NP', 'APN', 'PA', 'DMD']
        case_type_list = ["Revocation of Practitioner's Registration, Denial of Application for Exporter's Registration", 'Denial of Application for Fees and Expenses Under the Equal Access to Justice Act', 'Revocation of Registration, Denial of Request for Change of Registered Location', 'Order Regarding Officially Noticed Evidence and Motion for Reconsideration', 'Order Rescinding Final Order Denying Application for Registration', 'Revocation of Registration and Denial of Application - Correction', 'Order Accepting Settlement Agreement and Terminating Proceeding', 'Denial of Request for Registration To Handle List I Chemicals', 'Denial of Request for Registration to Handle List I Chemicals', 'Declaratory Order Terminating Exemption From Registration', 'Grant of Renewal Application and Dismissal of Proceeding', 'Denial of Application for Change of Registered Address', 'Revocation of Registration and Denial of Application', 'Granting of Renewal Application Subject to Condition', 'Grant Registration to Import Schedule II Substances', 'Affirmance of Immediate Suspension of Registration', 'Denial of Request for Modification of Registration', 'Continuation of Registration with Restrictions', 'Continuation of Registration With Restrictions', 'Notice of Withdrawal of Denial of Application', 'Declaratory Order Terminating Registrations', 'Revocation of   Registration', 'Denial of Application for DEA Registration', 'Declaratory Order Terminating Registration', 'Affirmance of Immediate Suspension Order', 'Denial of Application for Registration', 'Revocation and Denial of Registration', 'Order Dismissing Order To Show Cause', 'Introduction and Procedural History', 'Affirmance of Immediate Suspension', 'Denial of Application (Correction)', 'Denial of Application- Correction', 'Grant of Conditional Registration', 'Denial of Request for Redactions', 'Grant of Restricted Registration', 'Decision and Order - Correction', 'Order Denying Procurement Quota', 'Affirmance of Suspension Orders', 'Affirmance of Suspension Order', 'Order Terminating Registration', 'Denial of Request for Hearing', 'Continuation of Registration', 'Revocation of Registrations', 'Suspension of Registration', 'Revocation of Registration', 'Denial of Motion for Stay', 'Admonition of Registrant', 'Change in Effective Date', 'Dismissal of Proceedings', 'Suspension Registration', 'Suspension of Shipments', 'Dismissal of Proceeding', 'Denial of Applications', 'Denial of Registration', 'Denial of Application', 'Denial Of Application', 'Orders to Show Cause', 'Grant of Application', 'Decision and Orders', 'Decision And Order', 'Procedural History', 'Decision and Order', 'Declaratory Order', 'Notice of Hearing', 'Order']
        formated_name, case_type, case_type_sep = '', '', ''
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
            if case_type: case_type_sep = ';'
        elif ':' in name:
            formated_name, case_type = name.rsplit(':', 1)
            case_type_sep = ':'
            # doctor_details_list = name.split(';')[:-1]
        if any(ele in formated_name for ele in case_type_list) or not formated_name:
            for each_case in case_type_list:
                if each_case in name:
                    if case_type_sep and each_case != case_type.strip():
                        case_type = each_case + '%s' %case_type_sep + case_type
                        formated_name = formated_name.replace(each_case, '').strip(', ')
                        break
                    elif not case_type_sep:
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
                for designation_chk in designation_check_re:
                    if designation_chk in person_name:
                        person_name = person_name.replace(designation_chk, '').strip()
                first_name, middle_name, last_name = self.personNameFormat(person_name)
                main_page_details.update({'firstName': first_name.strip(), 'middleInitial': middle_name.strip(), 'lastName': last_name.strip(), 'personName': person_name, 'doctorType': ', '.join(degree_types)})
            else:
                pass
        elif business_check and not person_check:
            if ' d/b/a ' in formated_name or 'D/B/A' in formated_name:
                if ' d/b/a ' in formated_name:
                    split_string = 'd/b/a'
                elif 'D/B/A' in formated_name:
                    split_string = 'D/B/A'
                org_name, entity_name = formated_name.split(split_string)
                org_name = org_name.strip('/ ')
                entity_name = entity_name.strip('/ ')
                if not any(ele in org_name for ele in business_type_list):
                    first_name, middle_name, last_name = self.personNameFormat(org_name.strip())
                    main_page_details.update({'firstName': first_name.strip(), 'middleInitial': middle_name.strip(), 'lastName': last_name.strip(), 'personName': org_name})
                    formated_name = entity_name.strip()
            main_page_details['businessName'] = formated_name
        else:
            main_page_details['title'] = formated_name
        main_page_details['typeOfCase'] = case_type.replace('\r\n ', '').strip()
        try:
            main_page_details['casePostDate'] = str(datetime.strptime(date, '%B %d, %Y').date())
        except:
            try:
                main_page_details['casePostDate'] = str(parse(date).date())
            except:
                pass
        if file_year:
            main_page_details.update({'dataFileYear': file_year})
        return main_page_details

    def get_data(self, obj):
        data, person_details = {}, {}
        for d in self.get_data_list(obj):
            da = d.json
            basic_details = da.get('basic_details', {})
            if basic_details:
                details = self.details(basic_details['name'], basic_details['date'], basic_details['file_year'])
                IndividualPersonTypeData(details)
                person_details.update(details)
                data.update({'basic_details': person_details})
            elif d.name == 'dea_meta':
                self.get_last_record_status(obj, da)
                if not da.get('typeofCase'): da['typeofCase'] = person_details.get('typeOfCase', '')
                if not da.get('dataFileYear'): da['dataFileYear'] = person_details.get('dataFileYear', '')
                if not da.get('casePostDate'): da['casePostDate'] = person_details.get('casePostDate', '')

                if (not da['personName']) and (person_details.get('firstName') or \
                        person_details.get('lastName') or person_details.get('middleInitial')):
                    da['personName'] = {'firstName': person_details.get('firstName'),
                                        'lastName':  person_details.get('lastName'),
                                        'middleInitial' : person_details.get('middleInitial'),
                                        'personFullName': person_details.get('personName')}

                    da['involvedCaseEntityType'] = 'individual'
                    if person_details.get('personTypeAcronym', ''):
                        da['personTypeAcronym'] = person_details.get('personTypeAcronym', '')
                        if da['personTypeAcronym']:
                            da['individualPersonType']   = person_details.get('individualPersonType', '')
                if person_details.get('businessName', ''):
                    da['involvedCaseEntityType']  = person_details.get('involvedCaseEntityType', 'business')
                    da['businessName'] = person_details.get('businessName', '')
                    if da['involvedCaseEntityType'] == 'business':
                        business_type_match = {
                                'Pharmacy': 'Pharmacy', 'Inc':	'Corporation',
                                'Corp': 'Corporation', 'LLC': 'Limited Liability Company',
                                'Diagnostic': 'Diagnostic', 'Wholesale': 'Wholesale',
                                'Pharmaceutical': 'Pharmaceutical', 'Trading Company': 'Trading Company',
                                'Distributing': 'Distributor', 'Distributor': 'Distributor',
                                'Home Health Services': 'Home Health Services', 'Shoppe/Shop': 'Shop',
                                'Enterprises': 'Enterprise', 'Shop': 'Shop', 'Farmacia': 'Pharmacy',
                                'Drug': 'Drug Company', 'Trading': 'Trading Company'
                        }
                        for key in business_type_match:
                            if key in da['businessName'].replace('.', ''): 
                                da['businessType'] = business_type_match[key]
                                break
                if not da.get('involvedCaseEntityType') and details.get('title'):
                    if " his " in da['caseSummary'][:1000] or " her " in da['caseSummary'][:1000]:
                        da['involvedCaseEntityType'] = 'individual'
                        first_name, middle_name, last_name = self.personNameFormat(details.get('title'))
                        da['personName'] = {'firstName': first_name.strip(), 'middleInitial': middle_name.strip(),
                            'lastName': last_name.strip(), 'personName': details.get('title')}
                    else:
                        da['businessName'] = details.get('title')
                        da['involvedCaseEntityType'] = 'business'
                data.update(da)
                if data.get('basic_details'):
                    data.pop('basic_details')
            elif d.name == 'georgia_meta':
                self.get_last_record_status(obj, da)
                data.update(generate_graduation_info(da))
                data = generate_primary_speciality(data)
                data = generate_final_output(data)
            elif d.name is '':
                if len(self.get_data_list(obj)) == 1:
                    if da.get('licenseNumber', ''):
                        da = suffixFormation(da)
                data.update(da)
            else:
                data.setdefault(d.name, []).append(da)
        return data

    def get_last_record_status(self, obj, data):
        first_scraped_at = obj.created_at.date()
        last_scraped_at = obj.last_scraped_at.date()
        recent_checked_at = obj.updated_at.date()
        max_updated_at = DetailTerminal.objects.aggregate(Max('updated_at'))
        max_updated_at = max_updated_at['updated_at__max'].date()
        if first_scraped_at == last_scraped_at == recent_checked_at:
            last_record_status = 'Added'
        elif max_updated_at - recent_checked_at >= timedelta(days=14):
            last_record_status = 'Deleted'
        elif last_scraped_at != recent_checked_at:
            last_record_status = 'No Change'
        elif last_scraped_at == recent_checked_at:
            last_record_status = 'Record Updated'

        data['lastRecordDataStatus'] = last_record_status
        data['firstRecordScrapeDate'] = str(first_scraped_at)
        data['lastRecordScrapeDate'] = str(last_scraped_at)

    class Meta(BaseItemDetailSerializer.Meta):
        model = DetailTerminal
        fields = ['source', 'key', 'url', 'active', 'data']

    def get_university(self, obj):
        university = obj.course_browse_items.first().university_items.first()
        return ListingTerminalItemKeySerializer(university).data

def IndividualPersonTypeData(details):
    doctor_type = details.get('doctorType', '')
    business_name = details.get('businessName', '')
    doctor_type_dict = {
        'PhD': 'Doctor of Philosophy',
        'DPM': 'Doctor Of Podiatric Medicine',
        'NP': 'Nurse Practitioner',
        'MD': 'Medical Doctor',
        'RN/APN': 'Advanced Practice Nurse, Registered Nurse',
        'FNP, RN': 'Family Nurse Practitioner, Registered Nurse',
        'F.N.P': 'Family Nurse Practitioner',
        'PA': 'Physician Assistant',
        'APN': 'Advanced Practice Nurse',
        'DDS': 'Doctor Of Dental Surgery',
        'DVM': 'Doctor Of Veterinary Medicine',
        'ARNP': 'An Advanced Registered Nurse Practitioner',
        'APRN': 'Advanced Practice Registered Nurse',
        'DMD': 'Doctor Of Medicine In Dentistry',
        'DO': 'Doctor of Osteopathic Medicine'
    }
    IndividualPersonType = doctor_type_dict.get(doctor_type, '')
    if IndividualPersonType:
        details.update({'individualPersonType': IndividualPersonType,
                        'personTypeAcronym': details.get('doctorType', ''),
                       })
    elif business_name and (not details.get('firstName') and not details.get('middleInitial') and not details.get('lastName')):
        details.update({'involvedCaseEntityType': 'business'})
