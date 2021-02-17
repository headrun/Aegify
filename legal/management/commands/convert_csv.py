from django.core.management.base import BaseCommand, CommandError
from legal.models.browse import *
from legal.models.detailterminal import *
from legal.api.serializers import *

from django.apps import apps

from datetime import datetime

import csv, os, json

class Command(BaseCommand):
    help = "Converts the crawled data into csv file"

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
        parser.add_argument('-p', '--output-path', type=str)
        parser.add_argument('-m', '--model', type=str)
        parser.add_argument('--serializer')

    def handle(self, *args, **kwargs):
        source = kwargs.get('source')
        path = kwargs.get('output_path')
        Serializer = globals()[kwargs.get('serializer')]
        Model = apps.get_model('legal', kwargs.get('model'))
        directory_path = os.path.join(path, datetime.now().strftime('%Y%m%d'))
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)
        filename = self.csvfilename_mapping.get(source) + '.csv'
        csvpath = os.path.join(directory_path, filename)

        queryset = Model.objects.select_related('source').filter(source__name=source)
        fieldnames = list()
        diff = list()
        for obj in queryset:
            data = json.dumps(Serializer(obj).data)
            json_data = json.loads(data, strict=False)
            field_keys = list(self.get_leaves(json_data).keys())
            if not fieldnames:
                fieldnames = field_keys
            else:
                diff = self.Diff(field_keys, fieldnames)
            if diff:
                fieldnames += diff

        with open(csvpath, 'w', newline='') as f_output:
            csv_output = csv.DictWriter(f_output, delimiter=",", fieldnames=fieldnames, extrasaction='ignore')
            csv_output.writeheader()

            queryset = Model.objects.select_related('source').filter(source__name=source)
            for obj in queryset:
                data = json.dumps(Serializer(obj).data)
                json_data = json.loads(data, strict=False)
                csv_output.writerow(self.get_leaves(json_data))

    def Diff(self, field_keys, fieldnames):
        return (list(set(field_keys)-set(fieldnames)))

    def get_leaves(self, item, key=None, key_prefix=""):
        if isinstance(item, dict):
            leaves = {}
            for item_key in item.keys():
                if item_key == 'zip_code':
                    item['zip_code'] = '`' + item[item_key] + '`' if item[item_key] else None
                if item_key == 'businessTelephone' and item[item_key] == '0000000000':
                    item['businessTelephone'] = '`' + item[item_key] + '`'
                temp_key_prefix = (
                    item_key if (key_prefix == "") else (key_prefix + "." + str(item_key))
                )
                leaves.update(self.get_leaves(item[item_key], item_key, temp_key_prefix))
            return leaves
        elif isinstance(item, list):
            leaves = {}
            elements = []
            for element in item:
                if len(item) == 1:
                    if (isinstance(element, dict) or isinstance(element, list)):
                        leaves.update(self.get_leaves(element, key, key_prefix))
                    elif isinstance(element, str):
                        elements.append(element)
                else:
                    elements.append(element)
            if len(elements) > 0:
                leaves[key_prefix] = elements
            return leaves
        else:
            return {key_prefix: item}





