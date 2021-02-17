import json
from datetime import datetime
import re
import textract
from tempfile import NamedTemporaryFile
from collections import OrderedDict, defaultdict
from dateutil.parser import parse
from ...validators import CasesAgainstDoctors

from . import *

class MainPage(BasePage):
    def request(self):
        url = self.url
        return Request(url)

    def update_data_dict(self, data_values):
        fed_reg_reference, fed_reg_post_date, federal_pages, federal_doc_no,\
        case_summary, findings, order, fed_reg_doc_reference, \
        fed_reg_filed_date, fed_reg_filed_time, administrative_authority, \
        billing_code, order_info_additional, sanctions = data_values
        data_dict = {}
        if fed_reg_reference:
            data_dict['federalRegisterReference'] = fed_reg_reference
        if fed_reg_post_date:
            data_dict['federalRegisterPostDate'] = parse(fed_reg_post_date)
        if federal_pages:
            data_dict['federalRegisterPages'] = federal_pages
        if case_summary:
            case_summary = [''.join(ele) for ele in case_summary]
            data_dict['caseSummary'] = "".join(case_summary)
        if findings:
            findings = [''.join(ele) for ele in findings]
            try:
                findings_data = ''.join(findings[1:])
            except:
                findings_data = ''
            data_dict['findingsofFact'] = findings_data
        if sanctions:
            sanctions = [''.join(ele) for ele in sanctions]
            sanctions_data =  ''.join(re.findall('^Sanction(.*)', ''.join(sanctions)))
            data_dict['sanctions'] = sanctions_data
        if order:
            order = [''.join(ele) for ele in order]
            order_data = ''.join(re.findall('[\w\.]?Order\,(.*)', ','.join(order))) or ''.join(re.findall('[\w\.]?ORDER\,(.*)', ','.join(order)))
            data_dict['order_info'] = order_data
        if administrative_authority:
            data_dict['administrativeAuthority'] = administrative_authority
        if fed_reg_doc_reference:
            data_dict['federalRegisterDocumentNumber'] = fed_reg_doc_reference
        if fed_reg_filed_date:
            data_dict['federalRegisterFileDate'] = parse(fed_reg_filed_date)
        if fed_reg_filed_time:
            data_dict['federalRegisterFileTime'] = fed_reg_filed_time
        if billing_code:
            data_dict['billingCode'] = ''.join(billing_code)
        if order_info_additional:
            data = ''.join([''.join(ele) for ele in order_info_additional])
            data_dict['additionalInfo'] = {'additionalInformation':data}
        return data_dict

    def fetch_data_from_root_node(self, sel_node):
        sel_node_child_tags = sel_node.xpath('./*')
        data_dict = {}
        fed_reg_reference, fed_reg_post_date, federal_pages, federal_doc_no = [''] * 4
        fed_reg_doc_reference, fed_reg_filed_date, fed_reg_filed_time = [''] * 3
        case_summary = []
        findings = []
        sanctions = []
        order = []
        header_flag, case_summary_flag, findings_flag, order_flag, sanctions_flag = [0] * 5
        billing_code = '', ''
        prvious_node = ''
        administrative_authority = {}
        order_info_additional = []
        for child_tag in sel_node_child_tags:
            tag = re.findall('<(\w+\d*)\s?.*?>', ''.join(child_tag.extract()))[0]
            fed_doc_check = sel_node_child_tags.index(child_tag) >= len(sel_node_child_tags)-3
            raw_html_value = child_tag.extract()
            text_value = []

            #
            if raw_html_value.startswith('<p>'):
                text_value = [self.clean_string(''.join(child_tag.xpath('.//text()').extract()))]
            elif not raw_html_value.startswith('<p>'):
                text_value = [self.clean_string(''.join(x.xpath('.//text()').extract())) for x in child_tag.xpath('./p')]
            #Federal Register related data population logic starts
            if "Federal Register" in raw_html_value:
                fed_reg_re = re.findall('\[?Federal Register(\s|\:)?(.*?)\s?\((\w?.*?)\)\]', raw_html_value) or re.findall('\[Federal Register(\s|\:)?(.*?)<br>?[\\r\\n]?\s*\((\w?.*?)\)\]', raw_html_value)
                if fed_reg_re:
                    fed_reg_reference, fed_reg_post_date = fed_reg_re[0][-2:]
                else:
                    fed_reg_re = re.findall('\[Federal Register\:\s?(\w+\s\d+, \d{4})\s\((.*)\)\]', raw_html_value)
                    if fed_reg_re:
                        fed_reg_post_date, fed_reg_reference = fed_reg_re[0]
                if 'volume' in fed_reg_post_date.lower():
                    fed_reg_post_date, fed_reg_reference = (fed_reg_reference, fed_reg_post_date)
                pages_re = re.findall('\[Pages?\s*(\d+-?\d+)\]', raw_html_value)
                if pages_re:
                    federal_pages = pages_re[0]
                federal_doc_no_re = re.findall('\[FR Doc No:\s?(\d+-?\d+)\]', raw_html_value) or re.findall('\[DOCID:\s?(\w+-?\w+)\]', raw_html_value)
                if federal_doc_no_re:
                    federal_doc_no = federal_doc_no_re[0]
            elif 'BILLING' in raw_html_value:
                billing_code = raw_html_value.replace('  ', '').split('BILLING CODE ')[-1].split('<')[0]
            #federal register data at bottom
            #in some cases Administrator is not being populated handling such based on fr_doc previous node
            if (administrative_authority or order_flag) or fed_doc_check:
                if '[FR Doc.' in raw_html_value:
                    if order_flag or fed_doc_check:
                        order_flag, findings_flag, case_summary_flag, header_flag, sanctions_flag = [0]*5
                        administrative_authority = self.fetch_admin_authority_dict(previous_tag)
                    fed_reg_bottom_data_re = re.findall('\[FR\s\Doc\.\s?(\w+-\d+)\s*Filed\s*\-?(\d+-\d+-\d+);\s*?(\d+:\d+\s?\w+)\]', raw_html_value) or re.findall('\[FR\s\Doc\.\s?(\d+-\d+)\s*Filed\s*(\d+-\d+-\d+)\;?\s*?(\d+:\d+\s?\w+)?\]?', raw_html_value)
                    if not fed_reg_bottom_data_re:
                        fed_reg_bottom_data_re = re.findall('\[FR\s\Doc\.\s?(\w+-\d+)\s*Filed\s*(\d+-\d+-\d+);\s*?(\d+:\d+\s?\w+)\]', raw_html_value)
                    if fed_reg_bottom_data_re:
                        fed_reg_doc_reference, fed_reg_filed_date, fed_reg_filed_time = fed_reg_bottom_data_re[0]
                        try:
                            fed_reg_filed_date = datetime.strptime(fed_reg_filed_date, '%m-%d-%y').strftime('%m/%d/%Y')
                        except:
                            fed_reg_filed_date = ''
                        try:
                            fed_reg_filed_time = datetime.strptime(fed_reg_filed_time, '%I:%M %p').strftime('%H:%M')
                        except:
                            try:
                               fed_reg_filed_time = datetime.strptime(fed_reg_filed_time, '%I:%M%p').strftime('%H:%M')
                            except:
                                fed_reg_filed_time = ''
                elif administrative_authority:
                    if text_value:
                        order_info_additional.append(text_value)
            #Federal register data population ends

            #identifying the Fed register data separator with header tag
            if '<hr>' in raw_html_value:
                header_flag = 1

            #checking for case summary
            if header_flag and '<p>' in raw_html_value and '<p><strong>' not in raw_html_value:
                case_summary_flag = 1
                header_flag = 0
            elif not header_flag and '<p>' in raw_html_value and '<p><strong>' not in raw_html_value:
                if 'Order' in re.findall('<p>\s?(\w+)\s?</p>', raw_html_value):
                    order_flag = 1
                    findings_flag, case_summary_flag, header_flag = [0] * 3
            elif not header_flag and '<p><strong>' in raw_html_value:
                if 'Findings' in raw_html_value:
                    findings_flag = 1
                    case_summary_flag = 0
                    header_flag = 0
                elif 'Order' in raw_html_value or 'ORDER' in raw_html_value:
                    order_flag = 1
                    findings_flag, case_summary_flag, header_flag = [0] * 3
                elif 'Sanction' in raw_html_value:
                    sanctions_flag = 1
                    findings_flag, case_summary_flag, header_flag = [0] * 3

                if order_flag and 'Acting Administrator' in raw_html_value:
                    order_flag, findings_flag, case_summary_flag, header_flag, sanctions_flag = [0]*5
                    administrative_authority = self.fetch_admin_authority_dict(child_tag)

            if case_summary_flag:
                case_summary_flag += 1
                if text_value:
                    case_summary.append(text_value)
            elif findings_flag:
                findings_flag += 1
                if text_value:
                    findings.append(text_value)
            elif order_flag:
                order_flag += 1
                if text_value:
                    order.append(text_value)
            elif sanctions_flag:
                sanctions_flag += 1
                if text_value:
                    sanctions.append(text_value)
            previous_tag = child_tag

        return [fed_reg_reference, fed_reg_post_date,
            federal_pages, federal_doc_no, case_summary, findings, order,
            fed_reg_doc_reference, fed_reg_filed_date, fed_reg_filed_time,
            administrative_authority, billing_code, order_info_additional, sanctions]

    def parse(self, response):
        sel = Selector(text=response.body)
        if response.url.endswith(".pdf"):
            #control_chars = ''.join(map(chr, chain(range(0, 9), range(11, 32), range(127, 160))))
            #CONTROL_CHAR_RE = re.compile('[%s]' % re.escape(control_chars))
            temp_file=NamedTemporaryFile(suffix=".pdf")
            temp_file.write(response.body)
            temp_file.flush()
            extracted_data=textract.process(temp_file.name)
            extracted_data=self.extracted_data_pdf(extracted_data.decode('utf-8'))
            #extracted_data=CONTROL_CHAR_RE.sub('',extracted_data)
            data_item = self.update_data_dict(extracted_data)
            try:
                case_year_url = response.url.strip('/').rpartition('/')[0] + '/index.html'
            except: case_year_url = ''
            data_item['caseYearURL'] = case_year_url
            data_item['caseRecordFileURL'] = response.url
            data_item['dataFileYear']      = ''
            self.kwargs['active'] = False
            temp_file.close()
            return CasesAgainstDoctors(data_item)

        data_file_year = ''
        data_file_year_xpath = "".join(response.xpath('//div[@class="sect_head_text"]//h1//text()').extract())
        if data_file_year_xpath:
            data_file_year = "".join(re.findall('\d{4}', data_file_year_xpath))
        case_year_url = "".join(response.xpath('//div[@class="crumb_head"]//p//a[contains(text(), "Registrant")]//@href').extract())
        if case_year_url:
            case_year_url = response.url.strip('/').rpartition('/')[0] + '/' +  case_year_url
        page_content_node = sel.xpath('//div[@class="page_content"]')
        #parsed_data_list, raw_data_list = self.fetch_data_from_root_node(page_content_node)
        data_list = self.fetch_data_from_root_node(page_content_node)
        data_item = self.update_data_dict(data_list)
        data_item['caseYearURL'] = case_year_url
        data_item['caseRecordFileURL'] = response.url
        data_item['dataFileYear']      = data_file_year
        self.kwargs['active'] = False
        #return CourseSchemaItem(courseData)
        return CasesAgainstDoctors(data_item)

    def fetch_admin_authority_dict(self, node):
        administrator = self.clean_string(''.join(node.xpath('./strong/text()').extract())).strip(', ')
        authority = self.clean_string(''.join(node.xpath('./em/text()').extract()))
        if administrator and authority:
            return {'authority_order': authority.strip('. '),
                    'name': administrator}
        else:
            return {}

    def extracted_data_pdf(self, extracted_data):
        data = extracted_data.replace('\n','')
        fed_reg_reference, fed_reg_post_date, federal_pages, federal_doc_no = [''] * 4
        fed_reg_doc_reference, fed_reg_filed_date, fed_reg_filed_time = [''] * 3
        case_summary, findings, order, sanctions = [], [], [], []
        administrative_authority, billing_code, order_info_additional = {}, '', {}
        case = re.findall('(DEPARTMENT OF JUSTICE\nDrug Enforcement Administration.*)\nDEPARTMENT OF JUSTICE\nDrug Enforcement Administration',extracted_data,re.DOTALL) or re.findall('(DEPARTMENT OF JUSTICE\nDrug Enforcement Administration.*?\nBILLING CODE.*\n?)',extracted_data,re.DOTALL)
        if case:
            data = ''.join(case).split('BILLING CODE')[-1]
            required_data = case[0]
            if "Federal Register" in required_data:
                fed_reg_re = re.findall('Federal Register / (.*) / Notices', required_data)[0].split('/')
                if fed_reg_re:
                    fed_reg_reference, fed_reg_post_date = fed_reg_re
                pages_re = re.findall('\[Pages?\s?(\d+–?\d+)\]', required_data)
                if pages_re:
                    federal_pages = pages_re[0]
                federal_doc_no_re = re.findall('\[FR Doc No:\s?(\d+–?\d+)\]', required_data)
                if federal_doc_no_re:
                    federal_doc_no = federal_doc_no_re[0]
            if 'BILLING CODE' in required_data:
                billing_code = re.findall('BILLING CODE(.*)', required_data)[0].strip()
            if '[FR Doc.' in required_data:
                fed_reg_bottom_data_re = re.findall('\[FR\s\Doc\.\s?(\d+–\d+)\sFiled\s(\d+–\d+–\d+);\s?(\d+:\d+\s?\w+)\]', required_data)
                if not fed_reg_bottom_data_re:
                    fed_reg_bottom_data_re = re.findall('\[FR\s\Doc\.\s?(\w+–\d+)\sFiled\s(\d+–\d+–\d+);\s?(\d+:\d+\s?\w+)\]', required_data)
                if fed_reg_bottom_data_re:
                    fed_reg_doc_reference, fed_reg_filed_date, fed_reg_filed_time = fed_reg_bottom_data_re[0]
                    try:
                        fed_reg_filed_date = datetime.strptime(fed_reg_filed_date, '%m–%d–%y').strftime('%m/%d/%Y')
                    except:
                        fed_reg_filed_date = ''
                    try:
                        fed_reg_filed_time = datetime.strptime(fed_reg_filed_time, '%I:%M %p').strftime('%H:%M')
                    except:
                        fed_reg_filed_time = ''

            # These cases for getting the data Form Pdf for authority. If required will enable these lines.

            #try:
                #admin_data = ''.join(re.findall('(\nDated:.*?)\nActing Administrator.', required_data, re.DOTALL)).split('\n')[-1].replace(',', '') or ''.join(re.findall('(\nDated:.*?)\nDeputy Administrator.', required_data, re.DOTALL)).split('\n')[-1].replace(',', '')
            #except:
                #admin_data = ''
            #administrative_authority = {'authority_order':'Acting Administrator', 'name':admin_data}
            # These cases for getting the data Form Pdf. If required will enable these lines.
            #case_summary = re.findall('(DEPARTMENT OF JUSTICE.*?)Findings of Fact',required_data,re.DOTALL) or re.findall('(DEPARTMENT OF JUSTICE.*?)Discussion',required_data,re.DOTALL) or re.findall('(DEPARTMENT OF JUSTICE.*?)\nOrder\n',required_data,re.DOTALL)
            #order = re.findall('(V. Order\n.*?)\nActing Administrator', required_data, re.DOTALL)
            #findings = re.findall(' Findings of Fact.*. Sanction', required_data) or re.findall('(Findings of Fact\n.*?)The Investigation\n',required_data,re.DOTALL) or re.findall('(Findings of Fact\n.*?)The Investigation of Respondent\n',required_data,re.DOTALL) or re.findall('(Findings of Fact\n.*?)The Dispensing Allegations\n',required_data,re.DOTALL) or re.findall('(Findings of Fact\n.*?)The DEA Investigation\n',required_data,re.DOTALL) or re.findall('(Findings of Fact\n.*?)\nThe Prior Criminal and Administrative\nProceedings',required_data,re.DOTALL) or re.findall('(Findings\n.*?)DEA Guidance to Distributors on\n',required_data,re.DOTALL) or re.findall('(Findings of Fact\n.*?)Discussion\n',required_data,re.DOTALL)
            #sanctions = re.findall('( Sanction\n.*?)\nV. Order', required_data, re.DOTALL) or re.findall('(\nSanction\n.*?)\nOrder\n', required_data, re.DOTALL)

        return [fed_reg_reference, fed_reg_post_date,
            federal_pages, federal_doc_no, case_summary, findings, order,
            fed_reg_doc_reference, fed_reg_filed_date, fed_reg_filed_time,
            administrative_authority, billing_code, order_info_additional, sanctions] 
    
    def clean_string(self, unclean_string):
        return unclean_string.replace('\r\n', '').replace('\t', '')\
            .replace('\n', '').replace('\xa0', ' ')\
            .replace('    ', ' ').replace('    ', ' ').strip()

class MySpider(BaseSpider):
    name = SOURCE + '_detail_terminal'
    source_name = SOURCE

    MODEL = 'DetailTerminal'
    main_page_class = MainPage
