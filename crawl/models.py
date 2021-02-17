import os

from django.db import models
from django.utils.functional import cached_property

from django_mysql.models import JSONField, ListTextField

from base.models import *

from .field import *

class Proxy(BaseModel):
    name            = models.CharField(
                        max_length=MAX_LENGTH_NAME,
                        unique=True
                    )
    headers         = JSONField(
                        null=True, blank=True,
                        help_text='{<br/>"Proxy-Authorization": "Basic xxxxxx",<br/> ...<br/>}'
                    )
    servers         = ListTextField(
                        base_field=models.CharField(max_length=MAX_LENGTH_LONG_NAME),
                        help_text='comma-separated urls.<br/>https://www.example.com:6060, ...<br/>'
                    )

    class Meta(BaseModel.Meta):
        pass

    def __str__(self):
        return '%s' % self.name

class SourceGroup(BaseGroupModel):
    headers         = JSONField(
                        null=True, blank=True,
                        help_text='{<br/>"key": "value",<br/> ...<br/>}'
                    )
    settings        = JSONField(
                        null=True, blank=True,
                        help_text='{<br/>"ROBOTSTXT_OBEY": false,<br/> ...<br/>}'
                    )

    class Meta(BaseGroupModel.Meta):
        unique_together = (('name', ), ('order', ))

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)

class SourceActiveManager(ActiveManager):
    def get_queryset(self):
        return super().get_queryset()

class BaseSource(TimeModel):
    name            = models.CharField(max_length=MAX_LENGTH_NAME)
    fullname        = models.CharField(max_length=MAX_LENGTH_MSG)
    url             = models.CharField(max_length=MAX_LENGTH_URL)

    active          = models.BooleanField(default=True)
    deployed        = models.BooleanField(default=True)

    proxy           = models.ForeignKey(Proxy, null=True, blank=True, on_delete=models.CASCADE, related_name='+')
    groups          = models.ManyToManyField(
                        SourceGroup,
                        blank=True,
                        related_name="%(app_label)s_%(class)ss",
                        related_query_name="%(app_label)s_%(class)ss"
                    )
    aka             = models.CharField(max_length=MAX_LENGTH_NAME, default='', blank=True)
    objects         = models.Manager()
    active_objects  = SourceActiveManager()

    class Meta(TimeModel.Meta):
        abstract = True
        unique_together = (('name', 'url'), )
        ordering = ('name',)

    def __str__(self):
        return self.name

    @classmethod
    def get_or_create_by_name(cls, name, do_create):
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist as e:
            if do_create:
                return cls.objects.create(name=name, fullname=name, url=name)
            raise e

    def set_group_values(self):
        self.headers, self.settings = {}, {}
        for group in self.groups.all():
            self.headers.update(group.headers)
            self.settings.update(group.settings)

class ItemActiveManager(ActiveManager):
    def get_queryset(self):
        return super().get_queryset().select_related('source').filter(source__active=True)

class BaseItemGroup(BaseGroupModel):
    key             = models.CharField(max_length=MAX_LENGTH_ID)

    class Meta(BaseGroupModel.Meta):
        abstract = True
        unique_together = (('name', 'key'), )

class BaseItem(TimeModel):
    KEY_FIELD_NAME  = 'key'

    key             = models.CharField(max_length=MAX_LENGTH_ID)
    url             = models.CharField(max_length=MAX_LENGTH_URL, default='')

    active          = models.BooleanField(default=True)
    status          = TruncatingCharField(max_length=MAX_LENGTH_MSG, null=True, blank=True)

    # Managers
    objects         = models.Manager()
    active_objects  = ItemActiveManager()
    latest_objects  = objects

    class Meta(TimeModel.Meta):
        abstract = True
        ordering = ('-created_at',)

    class InvalidDataException(Exception):
        """ data_list does not have valid data. """

    @classmethod
    def api_name(self):
        return self._meta.app_label

    @classmethod
    def is_valid_key(cls, key):
        return len(key) < cls.key.field.max_length

    @classmethod
    def latest_get_or_create(cls, **kwargs):
        return cls.latest_objects.get_or_create(**kwargs)

    def __str__(self):
        return '%s/%s' % (getattr(self, 'source', '?'), self.key)

class BaseData(TimeModel):
    #item           = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='data_list')

    name            = models.CharField(max_length=MAX_LENGTH_NAME, default='')
    order           = models.PositiveIntegerField(default=0)

    json            = JSONField()

    hashkey         = models.CharField(max_length=MAX_LENGTH_ID, default='')

    class Meta(TimeModel.Meta):
        abstract = True
        ordering = ('name', 'order', 'updated_at')

class BaseCrawlRun(BaseLogModel):
    #source          = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='crawl_runs')

    name            = models.CharField(max_length=MAX_LENGTH_NAME, default='--')
    msg             = TruncatingCharField(max_length=MAX_LENGTH_MSG)

    STATUS_LIST = ['Pending', 'Success', 'Failure']
    STATUS_PENDING, STATUS_SUCCESS, STATUS_FAILURE = range(len(STATUS_LIST))
    status          = models.CharField(max_length=MAX_LENGTH_SHORT_NAME, default=STATUS_PENDING, choices=[(i, x) for i, x in enumerate(STATUS_LIST)])

    stats           = JSONField()

    class Meta(BaseLogModel.Meta):
        abstract = True

    def status_str(self):
        return self.STATUS_LIST[int(self.status)]

class BaseLog(BaseLogModel):
    #crawl_run       = models.ForeignKey(CrawlRun, null=True, blank=True, on_delete=models.CASCADE, related_name='logs')

    STATUS_LIST = ['Pending', 'Success', 'Failure', 'FalsePositive']
    STATUS_PENDING, STATUS_SUCCESS, STATUS_FAILURE, STATUS_FALSEPOSITIVE = range(len(STATUS_LIST))
    status          = models.CharField(max_length=MAX_LENGTH_SHORT_NAME, default=STATUS_PENDING, choices=[(i, x) for i, x in enumerate(STATUS_LIST)])

    msg             = TruncatingCharField(max_length=MAX_LENGTH_MSG)

    spider          = models.CharField(max_length=MAX_LENGTH_NAME)

    #item            = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='logs')
    #parent_log      = models.ForeignKey('Log', on_delete=models.CASCADE, related_name='child_logs', null=True, blank=True)

    class Meta(BaseModel.Meta):
        abstract = True

    def __str__(self):
        return '%s/%s' % (getattr(self, 'item', ''), self.created_at)

    def status_str(self):
        return self.STATUS_LIST[int(self.status)]

class BaseUser(BaseItem):
    #username        = models.CharField(max_length=MAX_LENGTH_NAME)
    password        = models.CharField(max_length=MAX_LENGTH_NAME)

    class Meta(BaseItem.Meta):
        abstract = True
        #unique_together = (('source', 'username'), )
        indexes = [
            #models.Index(fields=['source', 'username']),
        ]

    @classmethod
    def random_user(cls, source):
        return cls.objects.filter(source=source).first()

    @cached_property
    def username(self):
        return self.key

    def get_data(self):
        return {
            'username': self.username,
            'password': self.password,
        }

class BaseBrowse(BaseItem):

    class Meta(BaseItem.Meta):
        abstract = True

class BaseMediaItem(BaseItem):
    file            = models.FileField(upload_to=upload_path, max_length=MAX_LENGTH_URL, null=True, blank=True)

    class Meta(BaseItem.Meta):
        abstract = True

    def upload_path(self, filepath):
        parent_obj = get_parent(self) or self
        return os.path.join('images', parent_obj.upload_prefix(filepath))

    def upload_prefix(self, filepath, **kwargs):
        return filepath
