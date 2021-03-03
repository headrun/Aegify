from . import *
from .browse import MainPage
from ...validators import GeorgiaSchema
from datetime import datetime

def cleanData(data):
    return data.replace('\xa0', '').replace('\t\n', '').replace('\n', ' ').replace('\t', ' ').strip()

class detailResultPage(BasePage):
    def request(self):
        request_data = data_from_unique_key(self.key)
        license_number = request_data.get('licenseNumber', '')
        records = self.response.xpath('//span[text()=%s]/../..'%license_number)
        keys = ['licenseType', 'status', 'licenseNumber', 'address']
        record_url = []
        for each_record in records:
            data = {}
            person_name = ''.join(each_record.xpath('./td/table/tr/td/a/text()').extract()).strip()
            data['personName'] = key_decryption(person_name)
            td_data = each_record.xpath('./td/span/text()').extract()
            index = 0
            for key in keys:
                if index < len(td_data):
                    data[key] = key_decryption(td_data[index])
                else:
                    data[key] = ''
                index = index + 1
            if data == request_data:
                record_url.append(''.join(each_record.xpath('./td/table/tr/td/a/@href').extract()).strip())
        try:
            url = SOURCE_URL + record_url[0]
        except:
            raise Exception("The given search is not valid")
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        return Request(url, headers=headers, dont_filter=True, meta={'cookiejar': self.cookiejar})
    
    def parse(self, response):
        if response.status in [302, 404]:
            raise Exception("Session has expired.")
        item = {}
        person_name = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "full_name")]/text()').extract()).strip()
        item["licenseType"] = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "license_type")]/text()').extract()).strip()
        item["designation"] = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "lic_degree_suffix")]/text()').extract()).strip()
        item["status"] = ''.join(response.xpath('//span[contains(@id, "label_status")]/../../td[@class="rdata"][1]/span/text()').extract()).strip()
        item["licenseNumber"] = license_number = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "license_no")]/text()').extract()).strip()
        item["profession"] = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "license_type")]/text()').extract()).strip()
        item["professionSubtype"] = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "secondary")]/text()').extract()).strip()
        issued_date = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "issue_date")]/text()').extract()).strip()
        if issued_date:
            try:item["licenseIssueDate"] = str(datetime.strptime(issued_date, '%m/%d/%Y'))
            except:pass
        expiry_date = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "_expiry")]/text()').extract()).strip()
        if expiry_date:
            try:item["licenseExpiryDate"] = str(datetime.strptime(expiry_date, '%m/%d/%Y'))
            except:pass
        #Specialties
        speciality_rows = response.xpath('//caption[contains(text(),"Specialties")]/following-sibling::tr')
        item["primarySpecialty"] = self.getTableData(speciality_rows, ('specialty', 'certifyingBoard', 'isPrimarySpecialty'))
        # address splitting
        street_address = ','.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "addr_line")]/text()').extract()).strip()
        item["streetAddress"] = street_address
        try:item["zipCode"] = int(re.findall('[0-9]{5}', street_address)[-1])
        except:pass
        try:item["state"] = re.findall('\s+[A-Z]{2}', street_address)[-1].strip()
        except:pass
        item["country"] = ''.join(response.xpath('//td[@class="rlabel"]/following-sibling::td/span[contains(@id, "country")]/text()').extract()).strip()
        item["county"] = ''.join(response.xpath('//td[@class="rdata"]/span[contains(@id, "county")]/text()').extract()).strip()
        #Related Licenses
        related_license_list = response.xpath('//table[@class="nosideborders"]/tr')
        related_license_data = []
        for each_license in related_license_list:
            license_data = {
                'relationship': ''.join(each_license.xpath('./td/table/tr/td/span[contains(@id, "_name")]/text()').extract()).strip(),
                'name': ''.join(each_license.xpath('./td/table/tr/td/span[contains(@id, "_licensee")]/text()').extract()).strip(),
                'licenseNumber': ''.join(each_license.xpath('./td/table/tr/td[@class="rdata"]/a[contains(@id, "license_no")]/text()').extract()).strip(),
                'licenseType': ''.join(each_license.xpath('./td/table/tr/td[@class="rdata"]/span[contains(@id, "lic_type")]/text()').extract()).strip(),
            }
            start_date = ''.join(each_license.xpath('./td/table/tr/td[@class="rdata"]/span[contains(@id, "date_of_association")]/text()').extract()).strip()
            if start_date:
                try:license_data['sinceDate'] = str(datetime.strptime(start_date, '%m/%d/%Y'))
                except:pass
            end_date = ''.join(each_license.xpath('./td/table/tr/td[@class="rdata"]/span[contains(@id, "date_of_expiration")]/text()').extract()).strip()
            if end_date:
                try:license_data['endDate'] = str(datetime.strptime(end_date, '%m/%d/%Y'))
                except:pass
            status = each_license.xpath('./td/table/tr/td[@class="rdata"]/span[contains(@id, "lic_status")]/text()').extract()
            if len(status) == 2:
                license_data['status'] = status[-1]
            license_list = any(license_data.values())
            if license_list:
                related_license_data.append(license_data)
        item['relatedLicenses'] = related_license_data
        #Date of Profile Submission or Latest Update
        profile_submission_date = ''.join(response.xpath('//th[text()="Date of Profile Submission or Latest Update"]/../following-sibling::tr/td/text()').extract()).strip()
        if profile_submission_date:
            try:item["profileSubmissionDate"] = str(datetime.strptime(profile_submission_date, '%m/%d/%Y'))
            except:pass
        #Initial Licensure
        try:
            license_ensure_state, license_issue_date, malpractice_coverage = response.xpath('//caption[contains(text(),"Initial Licensure")]/following-sibling::tr/td/text()').extract()
            if cleanData(license_ensure_state):
                try:item["initialLicensureState"] =  cleanData(license_ensure_state)
                except:pass
            if cleanData(license_issue_date):
                try:item["initialLicenseIssueDate"] = str(datetime.strptime(license_issue_date, '%m/%d/%Y'))
                except:pass
            item["malpracticeCoverage"] = cleanData(malpractice_coverage)
        except:pass
        document = response.xpath('//table[@role="presentation"]/tr/td/a[contains(@href, "document_id")]/../../../tr')
        if document:
            public_document = []
            for each_doc in document:
                public_document.append({
                    'documentURL': 'https://gcmb.mylicense.com/verification/' + ''.join(each_doc.xpath('./td/a/@href').extract()).strip(),
                    'documentType': ''.join(each_doc.xpath('./td[@class="rdata"]/span[contains(@id, "doctype")]/text()').extract()).strip()
                })
            item['publicDocuments'] = public_document
        #Practice Location History
        current_practice_location_list = response.xpath('//caption[contains(text(), "Practice Location History")]/following-sibling::tr')
        item["currentPracticeLocation"] = self.getTableData(current_practice_location_list, ('city', 'state', 'country', 'fromDate', 'toDate'))
        #Medicaid/Medicare
        try:
            accepting_medicaid_patients, accepting_medicare_patients = response.xpath('//caption[contains(text(),"Medicaid/Medicare")]/following-sibling::tr/td/text()').extract()
            item["acceptingMedicaidPatients"] = cleanData(accepting_medicaid_patients)
            item["acceptingMedicarePatients"] = cleanData(accepting_medicare_patients)
        except:
            pass
        disclaimer = ''.join(response.xpath('//span[@id="phys_profile_disclaimer"]/text()').extract()).strip()
        #Education/Certifications
        school_education_list = response.xpath('//caption[contains(text(), "Education/Certifications")]/following-sibling::tr')
        item["educationInfo"] = self.getTableData(school_education_list, ('schoolType', 'fromDate', 'toDate', 'graduated', 'schoolName'))
        medical_education_list = response.xpath('//caption[contains(text(), "Graduate Medical Education")]/following-sibling::tr')
        item["medicalEducationInfo"] = self.getTableData(medical_education_list, ('programType', 'hospitalName', 'fromDate', 'toDate', 'address', 'country', 'graduated'))
        # Current Hospital Privileges
        hospital_privileges = response.xpath('//caption[contains(text(),"Current Hospital Privileges")]/following-sibling::tr')
        item["currentHospitalPrivileges"] = self.getTableData(hospital_privileges, ('hospitalName', 'location'))
        #Final Disciplinary Action
        disciplinary_action_list = response.xpath('//caption[contains(text(),"Final Disciplinary Action")]/following-sibling::tr')
        item["disciplinaryAction"] = self.getTableData(disciplinary_action_list, ('actionAgency', 'actionDate', 'violationdescription', 'actionType', 'actionDescription'))
        #Hospital Privilege Revocations
        privilege_revocations = response.xpath('//caption[contains(text(),"Hospital Privilege Revocations")]/following-sibling::tr')
        item["privilegeRevocations"] = self.getTableData(privilege_revocations, ('hospitalName', 'revocationDate', 'violationDescription', 'actionType', 'actionDescription'))
        #Criminal Offenses
        crimical_offenses_list = response.xpath('//caption[contains(text(),"Criminal Offenses")]/following-sibling::tr')
        item["criminalOffensesStatus"] = self.getTableData(crimical_offenses_list, ('dateofOffense', 'jurisdiction', 'descriptionofOffense'))
        #arbitrationAwards
        arbitration_awards_list = response.xpath('//table[@id="udogrid_malp_judgement"]/tr')
        item["arbitrationAwards"] = self.getTableData(arbitration_awards_list, ('date', 'amount'))
        #settlementAmounts
        settlement_ammounts_list = response.xpath('//table[@id="udogrid_malp_settlement"]/tr')
        item["settlementAmounts"] = self.getTableData(settlement_ammounts_list, ('date', 'amount'))
        item["additionalInfo"] = {}
        #List of all languages excluding English used the by physician to communicate 
        languages = ','.join(response.xpath('//table[@id="udogrid_languages"]/tr/td/text()').extract()).strip()
        if languages:
            item["additionalInfo"]["knownLanguages"] = languages
        #List of physician's articles, journals, or publications limited to the most recent ten years
        publication_list = response.xpath('//table[@id="udogrid_publications"]/tr')
        publication = self.getTableData(publication_list, ('date', 'publication', 'title'))
        if publication:
            item["additionalInfo"]["publication"] = str(publication)
        #Physician's Comments
        physician_comments = response.xpath('//table[@id="udogrid_profile_comments"]/tr/td/text()').extract()
        if physician_comments:
            item["additionalInfo"]["physicianComments"] = ' '.join([ele for ele in physician_comments if ele.replace('\xa0', '')])
        #Membership in Professional Organizations/Community Service Organizations Status
        membership_in_organizations = response.xpath('//table[@id="udogrid_org_act"]/tr')
        item["membershipInOrganizations"] = self.getTableData(membership_in_organizations, ('organization', 'organizationType', 'description'))
        #awards
        award_list = response.xpath('//caption[contains(text(),"Awards")]/following-sibling::tr')
        item["awards"] = self.getTableData(award_list, ('organization', 'name'))
        #List of Appointments to Medical School Faculties
        medical_school_faculties = response.xpath('//th[text()="School"]/../following-sibling::tr')
        item["medicalSchoolFaculties"] = self.getTableData(medical_school_faculties, ('school_name', 'position'))
        return GeorgiaSchema(item)

    def getTableData(self, rows_list, titles):
        table_data = []
        for each_row in rows_list:
            column_data = each_row.xpath('./td/text()').extract()
            valid_list = any(s.strip() for s in column_data)
            if column_data and valid_list:
                try:
                    item = {}
                    for (key, value) in zip(titles, column_data):
                        if value and ('date' in key.lower() or 'graduated' in key.lower()):
                            try:item[key] = str(datetime.strptime(value, '%m/%d/%Y'))
                            except:pass
                        elif key == 'location':
                            city, state, zip_code = self.getAddress(value)
                            item.update({
                                'city': city.strip(),
                                'state_code': state.strip()
                            })
                            if zip_code:
                                try:
                                    item['zipCode'] = int(zip_code)
                                except:
                                    pass
                        else:
                            item[key] = cleanData(value)
                    table_data.append(item)
                except: pass
        return table_data

    def getAddress(self, location):
        city, state, zip_code = '', '', ''
        try:zip_code = int(re.findall('[0-9]{5}', location)[-1])
        except:pass
        try:state = re.findall('\s?\,?([A-Z]{2})', location)[-1].strip()
        except:pass
        if not state and not zip_code:
            city = location
        else:
            if state:
                try:city = location.split(state)[0].strip(', /')
                except:pass
            elif zip_code:
                try:city = location.split(str(zip_code))[0].strip(', /')
                except:pass
        return (city.strip(), state.strip(), zip_code)

class DetailListingPage(MainPage):
    next_class = detailResultPage
    page_type = 'terminalPage'

class GeorgiaTerminalSpider(BaseSpider):
    name = SOURCE + '_detail_terminal'
    source_name = SOURCE
    custom_settings = {"COOKIES_ENABLED":True}
    handle_httpstatus_list = [302]
    MODEL = 'DetailTerminal'
    main_page_class = DetailListingPage