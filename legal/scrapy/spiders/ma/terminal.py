from scrapy.selector import Selector
from crawl.scrapy.exceptions import FalsePositiveException
from . import *
from ...validators import Massachusetts


class MainPage(BasePage):
    def request(self):
        url = self.url or add_url(self.key)
        return Request(url)

    def parse(self, response):
        sel = Selector(response)
        try:
            person_info = person_data(clean_data(sel.xpath(person_xpath).extract()))
            aka = clean_data(sel.xpath("//div[contains(@class, 'name')]/div[@class='aka']/ul/li/text()").extract())
            licence_num = clean_data(sel.xpath(licence_xpath.format("License Number")).extract())
            licence_status = clean_data(sel.xpath(licence_xpath.format("License Status")).extract())
            licence_issue_dt = get_date(clean_data(sel.xpath(licence_xpath.format("License Issue Date")).extract()))
            licence_exp_dt = clean_data(sel.xpath(licence_xpath.format("License Expiration Date")).extract())
            revocation_date = clean_data(sel.xpath(licence_xpath.format("License Revocation Date")).extract())
            suspention_date = get_date(clean_data(sel.xpath(licence_xpath.format("License Suspension Date")).extract()))
            resigned_date = get_date(clean_data(sel.xpath(licence_xpath.format("Resigned Date")).extract()))
            retired_date = clean_data(sel.xpath(licence_xpath.format("Retired Date")).extract())
            primary_work = clean_data(sel.xpath(licence_xpath.format("Primary Work Setting")).extract())
            business_address = sel.xpath(licence_xpath.format("Business Address")).extract()
            if business_address:
                business_address = businessaddress(business_address)
            business_phone = clean_data(sel.xpath(licence_xpath.format("Business Telephone")).extract())
            accept_new_patients = clean_data(sel.xpath(licence_xpath.format("Accepting New Patients")).extract())
            if accept_new_patients == 'Yes':
                accept_new_patients = 'Y'
            elif accept_new_patients == 'No':
                accept_new_patients = 'N'
            accept_medicaid = clean_data(sel.xpath(licence_xpath.format("Accepts Medicaid")).extract())
            if accept_medicaid == 'Yes':
                accept_medicaid = 'Y'
            elif accept_medicaid == 'No':
                accept_medicaid = 'N'
            translation_services = clean_data(sel.xpath(licence_xpath.format("Translation Services Available")).extract())
            insurance_plans = clean_data(sel.xpath(licence_xpath.format("Insurance Plans Accepted")).extract())
            hsptl_aff = clean_data(sel.xpath(licence_xpath.format("Hospital Affiliations")).extract())
            npi_number = clean_data(sel.xpath(licence_xpath.format("NPI Number")).extract())
            graduation_dt = clean_data(sel.xpath(licence_sub_xpath.format("Graduation Date")).extract())
            medical_school = clean_data(sel.xpath(licence_sub_xpath.format("Medical School")).extract())
            post_training = sel.xpath(div_post_xpath.format("Post Graduate Training")).extract()
            try:
                designation = clean_data(sel.xpath(person_xpath).extract()).split(',')[-1].strip()
            except:
                designation = ''
            specialist = clean_data(sel.xpath(licence_sub_xpath.format("Area of Specialty")).extract())
            abms = False
            aoa = False
            abms = True if ''.join(sel.xpath(abms_xpath).extract()) else abms
            aoa = True if ''.join(sel.xpath(aoa_xpath).extract()) else aoa
            honors_awards = sel.xpath(div_award_xpath.format("Honors and Awards")).extract()
            prof_publications = [clean_data(x) for x in sel.xpath(div_award_xpath.format("Professional Publications")).extract() if x.strip()]
            boarddispline, board_certificates = [], []
            malpractice_claims = []
            board_nodes = sel.xpath('//div[@class="col-sm-12"]//table//tr')[1::]
            for board_node in board_nodes:
                board_name = clean_data(board_node.xpath('.//td[1]/text()').extract())
                general_certificate = clean_data(board_node.xpath('.//td[2]/text()').extract())
                sub_specialist = clean_data(board_node.xpath('.//td[3]/text()').extract())
                boardcertificates = {'boardName': board_name, 'generalCertification': general_certificate,
                                     'subspecialty': sub_specialist,
                                     'abmsBoardCertification': abms, 'aoaboardCertification': aoa}
                board_certificates.append(boardcertificates)

            malpracticeclaims = sel.xpath(malpractice_claims_xpath)
            for count, malpractice_claim in enumerate(malpracticeclaims):
                date = get_date(clean_data(malpractice_claim.xpath('.//td[1]/text()').extract()))
                category_pay = clean_data(malpractice_claim.xpath('.//td[2]/text()').extract())
                speciality = sel.xpath(malpractice_specialist).extract()
                if len(speciality) > 1:
                    try:
                        speciality = sel.xpath(malpractice_specialist).extract()[0].replace('Details for Payments in the ', '')
                        if len(malpracticeclaims.xpath('.//text()').extract()) % 2 == 0:
                            if count > 1:
                                speciality = sel.xpath(malpractice_specialist).extract()[1].replace('Details for Payments in the ', '')
                        else:
                            if count > 2:
                                speciality = sel.xpath(malpractice_specialist).extract()[1].replace('Details for Payments in the ', '')
                    except:
                        raise FalsePositiveException('exception in specialistdata')
                else:
                    speciality = sel.xpath(malpractice_specialist).extract()[0].replace('Details for Payments in the ', '')
                malpracticeclaim = {'date': date, 'categoryofPayment': category_pay, 'speciality': speciality}
                malpractice_claims.append(malpracticeclaim)
            crime_data, health_data, out_data = [], [], []
            mal_xpath = sel.xpath(mal_crime_xpath)
            
            if len(sel.xpath('//a[contains(@href, "Massachusetts_Criminal_Convictions_Pleas_and_Admissions")]//text()').extract()) > 1:
                crime_data = get_main_data(mal_xpath, "criminalconvictions")
            health_xpath = sel.xpath(hospital_xpath)
            if len(sel.xpath('//a[contains(@href, "Hospital_Discipline")]//text()').extract()) > 1:
                health_data_ = get_main_data(health_xpath, "healthcaredata")
                health_data = []
                for health_item in health_data_:
                    for key in health_item.keys():
                        if key not in ('facility', 'facilityType', 'actionBeginDate', 'actionEndDate', 'action', 'basisorAllegation'):
                            break
                    else:
                        health_data.append(health_item)

            out_of_board = sel.xpath(out_board_xpath)
            if len(sel.xpath('//a[contains(@href, "Out_of_State_Dicipline")]//text()').extract()) > 1 and len(sel.xpath('//a[contains(text(), "License Number")]//text()').extract()) > 1:
                out_data = get_main_data(out_of_board, "outstatediscipline")

            board_displine = sel.xpath(board_displine_xpath)
            if board_displine:
                for board_dis in board_displine:
                    date = get_date(clean_data(board_dis.xpath(board_xpath.format("Date")).extract()))
                    case = clean_data(board_dis.xpath(board_xpath.format("Case #")).extract())
                    action = board_dis.xpath(board_xpath.format("Action")).extract()
                    if len(clean_data(action).split(',')) >1:
                        action = clean_data(action[0])
                    else:
                        action = clean_data(action)
                    actionnote = clean_data(board_dis.xpath(board_xpath.format("Action Note")).extract())
                    instrument = clean_data(board_dis.xpath(board_xpath.format("Instrument")).extract())
                    fine_amount = clean_data(board_dis.xpath(board_xpath.format("Fine")).extract())
                    cost = clean_data(board_dis.xpath(board_xpath.format("Cost")).extract())
                    boarddispline_data = {'date': date, 'caseNumber': case, 'actionNote': actionnote,
                                          'action': action, 'instrument': instrument}
                    if cost:
                        boarddispline_data.update({'cost': cost})
                    if fine_amount:
                        boarddispline_data.update({'fineAmount': fine_amount})
                    boarddispline_data = remove_invalid_date_keys(boarddispline_data)
                    boarddispline.append(boarddispline_data)

            physician_data = {'personName': person_info, 'licenseNumber': licence_num, 
                              'licenseStatus': licence_status, 'licenseIssueDate': licence_issue_dt, 
                              'primaryWorkSetting': primary_work, 'designation': designation,
                              'businessAddress': business_address, 'areaofSpecialty': specialist,
                              'businessTelephone': business_phone, 'acceptingNewPatients': accept_new_patients,
                              'acceptsMedicaid': accept_medicaid, 'translationServicesAvailable': translation_services,
                              'insuranceplansAccepted': insurance_plans, 'hospitalAffiliations':hsptl_aff,
                              'medicalSchool': medical_school, 'postGraduateTraining': post_training,
                              'honorsandAwards': honors_awards, 'professionalPublications': prof_publications,
                              'npiNumber':npi_number, 'malpracticeclaims': malpractice_claims,
                              'criminalConvictions': crime_data,
                              'healthcarefacilityDiscipline': health_data,
                              'outofstateDiscipline': out_data,
                              'boarddiscipline': boarddispline,
                              'boardCertifications': board_certificates,
                              'suspensionDate': suspention_date,
                              'resignedDate': resigned_date,
                              'expireDate':get_date(licence_exp_dt),
                              'graduationDate': get_date(graduation_dt),
                              'revocationDate': get_date(revocation_date),
                              'retiredDate': get_date(retired_date)}
            physician_data = remove_invalid_date_keys(physician_data)
            if aka:
                physician_data['additionalInfo'] = {'aka': aka}
            yield Massachusetts(physician_data)
        except:
            raise FalsePositiveException('exception in data')

class MySpider(BaseSpider):
    name = SOURCE + '_terminal'
    source_name = SOURCE
    MODEL = 'ListingTerminal'
    main_page_class = MainPage
