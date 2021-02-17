from django.db import models

MAX_LENGTH_ID               = 64
MAX_LENGTH_LONG_ID          = 255
MAX_LENGTH_NAME             = 32
MAX_LENGTH_SHORT_NAME       = 16
MAX_LENGTH_LONG_NAME        = 64
MAX_LENGTH_URL              = 255
MAX_LENGTH_LONG_URL         = 1024
MAX_LENGTH_MSG              = 255
MAX_LENGTH_ADDRESS          = 255

class BaseModel(models.Model):

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.pk)

class BaseGroupModel(BaseModel):
    name            = models.CharField(
                        max_length=MAX_LENGTH_NAME
                    )
    order           = models.PositiveSmallIntegerField(
                        default=0,
                        help_text='higher order is higher precedence'
                    )

    class Meta:
        abstract = True
        ordering = ('order', )

    def __str__(self):
        return '%s' % self.name

class TimeModel(BaseModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BaseLogModel(TimeModel):

    class Meta(TimeModel.Meta):
        abstract = True

    def time_taken_in_sec(self):
        return (self.updated_at - self.created_at).seconds

def upload_path(obj, filepath):
    return obj.upload_path(filepath)

def get_parent(obj):
    for rel_obj in obj._meta._relation_tree:
        field = rel_obj.remote_field
        if field.parent_link:
            parent_obj = getattr(obj, field.name, None)
            if parent_obj:
                return parent_obj

