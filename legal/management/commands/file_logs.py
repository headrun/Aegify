from django.core.management.base import BaseCommand
from legal.models.browse import *
from legal.api.serializers import *
from django.db.models import Max
from django.apps import apps
from datetime import datetime, timedelta

import csv, os, json

class Command(BaseCommand):
    help = "Log file creator"

    csvfilename_mapping = {
        'dea': 'DEACriminalCasesAgainstDoctors_US_DEA',
        'ma': 'MA_MedicalRegistrationBoard_US_STATE',
        'clinicalinvestigators': 'FDADisqualifiedClinicalInvestigators_US_FDA',
        'florida': 'FL_MedicalLicensureBoard_US_STATE',
        'cms_npi': 'CMS_NPPES_US',
        'cms_medicare': 'CMS_OPTOUT_US',
        'georgia' : 'GA_MedicalLicenseStatus_BoardActions_US_STATE'
    }

    def add_arguments(self, parser):
        parser.add_argument('-s', '--source', type=str)
        parser.add_argument('-op', '--output-path', type=str)
        parser.add_argument('-lp', '--logs-path', type=str)

    def handle(self, *args, **kwargs):
        source = kwargs.get('source')
        output_path = kwargs.get('output_path')
        logs_path = kwargs.get('logs_path')
        directory_path = os.path.join(logs_path)

        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

        filename = self.csvfilename_mapping.get(source)+'_LOGS_'+str(datetime.now().strftime('%Y%m'))+ '.csv'
        csvpath = os.path.join(directory_path, filename)
        file_exists = os.path.isfile(csvpath)
        Model = apps.get_model('legal', 'crawlrun')
        queryset = Model.objects.select_related('source').filter(source__name=source)

        with open(csvpath, 'a', newline='') as f_output:
            writer = csv.DictWriter(f_output, delimiter=",",fieldnames=self.get_fields(source,None,None).keys(), extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            
            for obj in queryset:
                if not obj.is_logged:
                    crwalrun_created_at = obj.created_at
                    csv_info = self.get_csv_info(crwalrun_created_at,source,output_path)
                    data = self.get_fields(source, csv_info,obj)
                    writer.writerow(data)
                    obj.is_logged = True
                    obj.logged_at = datetime.now()
                    obj.save()

    def get_csv_info(self,date, source, output_path):
        if source == 'florida':
            directory = os.path.join(os.path.join(output_path, date.strftime('%Y%m%d')),source)
            if os.path.exists(directory):
                directory_info={}
                directory_info['type'] = "Directory"
                directory_info['name'] = source
                directory_info['created_at'] = datetime.fromtimestamp(os.path.getctime(directory))
                directory_info['modified_at'] = datetime.fromtimestamp(os.path.getmtime(directory))
                return directory_info
        else:
            file_name = os.path.join(os.path.join(output_path, date.strftime('%Y%m%d')),self.csvfilename_mapping.get(source))
            file_type=None
            if os.path.exists(file_name+'.csv'):
                file_type = 'CSV'
                file_path = file_name+'.csv'
            if os.path.exists(file_name+'.xls'):
                file_type = 'XLS'
                file_path = file_name+'.xls'
            
            if file_type:
                file_info={}
                file_info['type'] = file_type
                file_info['name'] = self.csvfilename_mapping.get(source)
                file_info['created_at'] = datetime.fromtimestamp(os.path.getctime(file_path))
                file_info['modified_at'] = datetime.fromtimestamp(os.path.getmtime(file_path))
                return file_info
        
    def get_last_record_status(self,source):
        try:
            model = apps.get_model('legal', 'detailterminal')
            obj = model.objects.select_related('source').filter(source__name= source).last()
            max_updated_at = DetailTerminal.objects.aggregate(Max('updated_at'))
            first_scraped_at = obj.created_at.date()
            last_scraped_at = obj.last_scraped_at.date()
            recent_checked_at = obj.updated_at.date()
            
            max_updated_at = max_updated_at['updated_at__max'].date()
            if first_scraped_at == last_scraped_at == recent_checked_at:
                last_record_status = 'Added'
            elif max_updated_at - recent_checked_at >= timedelta(days=14):
                last_record_status = 'Deleted'
            elif last_scraped_at != recent_checked_at:
                last_record_status = 'No Change'
            elif last_scraped_at == recent_checked_at:
                last_record_status = 'Record Updated'
            
            return last_record_status
        except:
            return ''

    def get_last_update_date(self,source):
        model = apps.get_model('legal', 'detailterminal')
        queryset = model.objects.select_related('source').filter(source__name= source).last()
        data = queryset.data_list.values()
        from_db_last_date=''
        if data:
            from_db_last_date = data[0].get('json', {}).get('last_modified_at', '')
        return from_db_last_date

    def get_fields(self,source, csv_info,crawl_run_obj ):
        data = {}
        data['File Type'] = csv_info.get('type','') if csv_info else ''
        data['File Name'] = csv_info.get('name','') if csv_info else ''
        
        if source=='dea':
            data['File Description']= 'This dataset provides a current and an UPDATED list of physicians registered with the DEA that have been involved in criminal activities. This is a listing of investigations of physician registrants in which DEA was involved that resulted in the arrest and prosecution of the registrant.'
            data['Source']= 'https://www.deadiversion.usdoj.gov/crim_admin_actions/index.html'
            data['Agency 1 Acronym']= 'USDEA'
            data['Agency 1 Name']= 'United States Drug Enforcement Administration'
            data['Agency 1 Type']= 'Federal'
            data['Agency 2 Acronym']= 'USDOJ'
            data['Agency 2 Name']= 'United States Department of Justice'
            data['Agency 2 Type']= 'Federal'
            data['Country']= 'USA'
            data['Data Scraper Check Frequency']='WEEKLY'
            data['Data Check Schedule']='Every Sunday at 12 Midnight'
            data['Update Date Available on Page']= 'NO'
            data['Data Scraper First Activation Date']= '2021-01-28 16:09:22.332572'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''       
            
        elif source =='ma':
            data['File Description']= 'This dataset provides a current and an UPDATED list of healthcare professionals in the State of Massachusetts with regards to their license status and any medical board related actions that might exist against them.'
            data['Source']= 'http://profiles.ehs.state.ma.us/ProfilesV3/FullSearch'
            data['Agency 1 Acronym']= 'MABM'
            data['Agency 1 Name']= 'Massachusetts Medical Board of Registration'
            data['Agency 1 Type']= 'State'
            data['Country']= 'USA'
            data['Update Date Available on Page']= 'NO'
            data['Data Scraper Check Frequency']='WEEKLY'
            data['Data Check Schedule']='Every Sunday at 12 Midnight'
            data['Data Scraper First Activation Date']= '2021-01-21 14:13:19.243344'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''
            
        elif source =='clinicalinvestigators':
            data['File Description']= 'This dataset provides a current and an UPDATED list that the FDA maintains of Clinical Investigators that have been disqualified for various reasons by the Agency.'
            data['Source']= 'https://www.accessdata.fda.gov/scripts/SDA/sdNavigation.cfm?sd=clinicalinvestigatorsdisqualificationproceedings&previewMode=true&displayAll=true'
            data['Agency 1 Acronym']= 'USDHHS'
            data['Agency 1 Name']= 'United States Department of Health & Human Services'
            data['Agency 1 Type']= 'Federal'
            data['Agency 2 Acronym']= 'USFDA'
            data['Agency 2 Name']= 'United States Federal Drug Agency'
            data['Agency 2 Type']= 'Federal'
            data['Country']= 'USA'
            data['Data Scraper Check Frequency']='NIGHTLY - Check to see if Update Date on Page is greater than the last date on page, Then Update.'
            data['Data Check Schedule']='Every Sunday at 12 Midnight (Server Time)'
            data['Update Date Available on Page']= 'YES'
            data['Data Scraper First Activation Date']= '2021-01-08 10:43:32.031980'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''
        
            data['Last Update Date on Page'] = self.get_last_update_date(source) if crawl_run_obj else ''
            data['File Update Status']= self.get_last_record_status(source) if crawl_run_obj else ''

        elif source =='florida':
            data['File Description']= 'This dataset provides a current and an UPDATED list of healthcare professionals in the State of Florida with regards to their license status and any medical board related actions that might exist against them.'
            data['Source']= 'https://mqa-internet.doh.state.fl.us/downloadnet/Licensure.aspx'
            data['Agency 1 Acronym']= 'FLMLB'
            data['Agency 1 Name']= 'Florida Medical Licensure Board'
            data['Agency 1 Type']= 'State'
            data['Country']= 'USA'
            data['Update Date Available on Page']= 'NO'
            data['Data Scraper Check Frequency']='WEEKLY'
            data['Data Check Schedule']='Every Sunday at 12 Midnight'
            data['Data Scraper First Activation Date']= '2021-01-08 11:29:38.443245'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''

        elif source =='cms_npi':
            data['File Description']= 'This dataset provides a current and an UPDATED list of healthcare professionals and providers in the United States with regards to their NPI information and status.'
            data['Source']= 'https://download.cms.gov/nppes/NPI_Files.html'
            data['Agency 1 Acronym']= 'CMS'
            data['Agency 1 Name']= 'Center for Medicare & Medicaid Services'
            data['Agency 1 Type']= 'Federal'
            data['Country']= 'USA'
            data['Update Date Available on Page']= 'NO'
            data['Data Scraper Check Frequency']='WEEKLY'
            data['Data Check Schedule']='Every Sunday at 12 Midnight'
            data['Data Scraper First Activation Date']= '2021-01-08 11:46:59.209091'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''

        elif source =='cms_medicare':
            data['File Description']= 'This dataset provides a current and an UPDATED list of healthcare professionals and providers in the United States with regards to their Medicare Opt Out information and status.'
            data['Source']= 'https://data.cms.gov/Medicare-Enrollment/Opt-Out-Affidavits/7yuw-754z'
            data['Agency 1 Acronym']= 'CMS'
            data['Agency 1 Name']= 'Center for Medicare & Medicaid Services'
            data['Agency 1 Type']= 'Federal'
            data['Country']= 'USA'
            data['Update Date Available on Page']= 'NO'
            data['Data Scraper Check Frequency']='WEEKLY'
            data['Data Check Schedule']='Every Sunday at 12 Midnight'
            data['Data Scraper First Activation Date']= '2021-01-11 03:14:11.226411'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''
      
        elif source =='georgia':
            data['File Description']= 'This dataset provides a current and an UPDATED list of healthcare professionals in the State of Georgia with regards to their license status and any medical board related actions that might exist against them.'
            data['Source']= 'https://gcmb.mylicense.com/verification/'
            data['Agency 1 Acronym']= 'GCMB'
            data['Agency 1 Name']= 'Georgia Composite Medical Board'
            data['Agency 1 Type']= 'State'
            data['Country']= 'USA'
            data['Update Date Available on Page']= 'NO'
            data['Data Scraper Check Frequency']='WEEKLY'
            data['Data Check Schedule']='Every Sunday at 12 Midnight'
            data['Data Scraper First Activation Date']= '2021-02-11 06:16:26.652590'
            data['Data Scraper Version Number']= ''
            data['Data Scraper Code Last Updated']= ''

        else:
            return

        data['File Creation Date/Time']= csv_info.get('created_at','') if csv_info else ''
        data['File Data Scraper ID']= crawl_run_obj.pk if crawl_run_obj else ''
        data['Last File Check Date/Time']= csv_info.get('modified_at','') if csv_info else ''
        data['Status']= crawl_run_obj.status_str() if crawl_run_obj else ''
        data['Fail Reason']= crawl_run_obj.msg if crawl_run_obj else ''

        return data