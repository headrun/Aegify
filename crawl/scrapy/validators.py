from hashlib import md5
from json import dumps

from django.utils import timezone
from django.utils.functional import cached_property

from schematics.undefined import Undefined
from schematics.models import Model
from schematics.types import *

class SchemaItemGroup(Model):
    name    = StringType(required=True)
    keys    = ListType(StringType)

    def key(self, k):
        keys = [k] + self.keys
        keys.sort()
        return keys[0]

class BaseSchemaItem(Model):
    groups  = ListType(ModelType(SchemaItemGroup), default=[])

class HashSchemaItem(BaseSchemaItem):
    HASH_KEYS = ()

    @cached_property
    def hashkey(self):
        if not self.HASH_KEYS:
            return ''

        hash_dict = {x: self.fields[x].to_primitive(self.get(x)) for x in self.HASH_KEYS}
        return md5(dumps(hash_dict, sort_keys=True).encode('utf8')).hexdigest()

class HttpStatusSchemaItem(BaseSchemaItem):
    http_status = StringType(required=True)
    time        = UTCDateTimeType(required=True, default=timezone.now)

    http_status_default = Undefined

    def __init__(self, *args, **kwargs):
        if self.http_status_default:
            self.fields['http_status']._default = self.http_status_default
        super().__init__(*args, **kwargs)

class OKSchemaItem(HttpStatusSchemaItem):
    http_status_default = '200'

class InvalidSchemaItem(HttpStatusSchemaItem):
    http_status_default = '204'

