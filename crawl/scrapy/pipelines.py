# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os, traceback
from datetime import datetime, timedelta, timezone

from django.core.exceptions import FieldDoesNotExist, MultipleObjectsReturned

from base.utils import makedir_p, get_media_path
from base.settings import DjangoUtil;
settings = DjangoUtil.settings()

from .validators import *

class DjangoPipeline(object):
    def process_item(self, data, spider):
        item_log, item_data = data['item_log'], data['data']
        item = item_log.item

        if isinstance(item_data, dict) and 'path' in item_data:
            path = os.path.join(settings.MEDIA_ROOT, get_media_path(item_data['path']))
            makedir_p(os.path.dirname(path))
            with open(path, 'wb') as f:
                f.write(item_data['data'])

            return
        
        ds = spider.settings.get('DEACTIVATED_AGAINST_STATUS',0)
        try:
            if ds and item.created_at < datetime.now(timezone.utc) - timedelta(days=ds):
                item.active = False
            self.save_item_data(item, item_data)

            self.update_spider(spider, item, data)

            self.update_item(item, data)

            item_log.status = item_log.STATUS_SUCCESS
        except Exception as e:
            traceback.print_exc()
            item_log.status = item_log.STATUS_FAILURE
            item_log.msg    = self.__class__.__name__ + ':' + str(e)
        item_log.save()

    def update_item(self, item, data):
        val = data['data']
        if 'active' in data:
            item.active = data['active']
        if isinstance(val, InvalidSchemaItem):
            item.active = False
            item.status = val.http_status
        item.save()

    def save_item_data(self, item, item_data):
        if not hasattr(item, 'data_list') or not item_data:
            return

        hashkey_exists = False
        try:
            item.data_list.field.model._meta.get_field('hashkey')
            hashkey_exists = True
        except FieldDoesNotExist:
            pass

        kwargs = {x: item_data.get(x, y) for x, y in (('name', ''), ('order', 0))}
        hashkey = item_data.get('hashkey', '')
        groups = item_data.get('groups', [])
        if isinstance(item_data, BaseSchemaItem):
            item_data.validate()
            item_data_dict = item_data.serialize()
        else:
            item_data_dict = item_data

        if 'groups' in item_data_dict and not groups:
            del item_data_dict['groups']
        self.save_item_groups(item, groups)

        obj = None
        for k in [''] + ([hashkey] if hashkey and hashkey_exists else []):
            if hashkey_exists:
                kwargs['hashkey'] = k
            try:
                obj = item.data_list.get(**kwargs)
            except item.data_list.field.model.DoesNotExist:
                continue
            break

        if obj:
            obj.json = item_data_dict
            if hashkey_exists:
                obj.hashkey = hashkey
            self.update_item_data(obj.__dict__, item_data)
            obj.save()
        else:
            kwargs['json'] = item_data_dict
            if hashkey_exists:
                kwargs['hashkey'] = hashkey
            self.update_item_data(kwargs, item_data)
            obj = item.data_list.create(**kwargs)
        return obj

    def save_item_groups(self, item, groups):
        if not hasattr(item, 'groups'):
            return

        for group in groups:
            keys = [item.key] + group.keys
            items = item.__class__.objects.filter(source=item.source, key__in=keys)
            group_model = item.groups.target_field.related_model
            try:
                obj, flag = group_model.objects.get_or_create(name=group.name, key=group.key(item.key))
            except MultipleObjectsReturned:
                obj = group_model.objects.filter(name=group.name, key=group.key(item.key)).order_by('id').first()
            obj.items.add(*items)

    def update_item_data(self, kwargs, item_data):
        return

    def update_spider(self, spider, item, data):
        spider.logger.info('Spider: %s, item: %s' % (spider.name, item))
