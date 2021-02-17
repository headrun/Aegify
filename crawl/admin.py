from urllib.parse import quote
from datetime import timedelta

from django.db.models import Prefetch
from django.contrib.admin import register, ModelAdmin, TabularInline
from django.utils.html import format_html, format_html_join
from django.urls import reverse

from .models import Proxy, SourceGroup, BaseSource

@register(Proxy)
class ProxyAdmin(ModelAdmin):
    list_display = ('name', 'headers', 'servers')

@register(SourceGroup)
class SourceGroupAdmin(ModelAdmin):
    list_display = ('order', 'name', 'headers', 'settings')
    ordering = ('-order', )

    
class BaseSourceAdmin(ModelAdmin):
    list_display = ('name', 'aka', 'active', 'deployed', 'proxy', 'headers', 'settings', 'group_names', 'url', 'fullname')
    list_filter = ('active', 'deployed', 'groups')
    filter_horizontal = ('groups',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('proxy').prefetch_related('groups')

    def group_names(self, obj):
        return ','.join([o.name for o in obj.groups.all()])

    def headers(self, obj):
        if not hasattr(obj, 'headers'):
            obj.set_group_values()
        return obj.headers

    def settings(self, obj):
        if not hasattr(obj, 'settings'):
            obj.set_group_values()
        return obj.settings

class BaseItemDataInline(TabularInline):
    fields = ('name', 'order', 'hashkey', 'json')
    readonly_fields = ('name', 'order', 'hashkey', 'json')

class BaseItemLogInline(TabularInline):
    fields = ('crawl_run', 'spider', 'status_str', 'message', 'created_at')
    readonly_fields = ('crawl_run', 'spider', 'status_str', 'message', 'created_at')

    def message(self, obj):
        try:
            return format_html(obj.msg.replace('\n', '<br />'))
        except:
            return obj.msg

class BaseItemAdmin(ModelAdmin):
    list_display = ('id', 'api', 'ref', 'source', 'key', 'active', 'status', 'created_at')
    fields = (('source', 'key'), 'ref', 'api', 'status', 'active')
    readonly_fields = ('api', 'source', 'key', 'ref', 'status')
    search_fields = ('source__name', 'key')
    list_filter = ('active', 'source', 'status')
    list_per_page = 10

    def api(self, obj):
        try:
            url = self.api_view.get_url(obj.source.name, quote(obj.key, safe=' '))
            return format_html('<a target="_blank" href="%s">View</a>' % url)
        except:
            return
    api.allow_tags=True

    def ref(self, obj):
        try:
            if obj.url:
                return format_html('<a target="_blank" href="%s">View</a>' % obj.url)
        except:
            return
    ref.allow_tags=True

class BaseUserAdmin(BaseItemAdmin):
    fields = ('source', ('key', 'password'), 'active', 'status')
    readonly_fields = ('status', )

class BaseBrowseAdmin(BaseItemAdmin):
    fields = (('source', 'key'), 'url', 'active', 'status')
    readonly_fields = ('status', )

class BaseCrawlRunAdmin(ModelAdmin):
    list_display = ('id', 'item_logs', 'source', 'name', 'status_str', 'duration', 'num_items', 'created_at', 'status_stats')
    fields = (('created_at', 'updated_at'), ('name', 'source'), ('status_str', 'msg'), ('num_items', 'duration', 'item_logs'), 'status_stats', 'crawl_stats')
    readonly_fields = ('created_at', 'updated_at', 'name', 'source', 'status_str', 'msg', 'num_items', 'duration', 'item_logs', 'status_stats', 'crawl_stats')
    list_filter = ('name', 'status', 'source', )
    list_per_page = 10

    LOGS_NAMES = ('item_logs', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        for logs_name in self.LOGS_NAMES:
            qs = self.prefetch_logs(request, qs, logs_name)
        return qs

    def duration(self, obj):
        return str(timedelta(seconds=obj.time_taken_in_sec()))

    def item_logs(self, obj):
        model_name = None
        for log_name in self.LOGS_NAMES:
            rel = getattr(obj, log_name)
            if rel.exists():
                model_name = rel.model._meta.model_name
                break
        if model_name:
            url = reverse('admin:%s_%s_changelist' % (obj._meta.app_label, model_name), args=[])
            url += '?crawl_run__id__exact=%d' % obj.id
            return format_html('<a target="_blank" href="%s">View</a>' % url)
    item_logs.allow_tags=True

    def prefetch_logs(self, request, qs, logs_name):
        log_model = getattr(self.model, logs_name).field.model
        qs = qs.prefetch_related(
                Prefetch(logs_name,
                    queryset=log_model.objects.only('crawl_run', 'status', 'item'),
                )
            )
        if request.resolver_match.func.__name__ == 'change_view':
            item_model = log_model.item.field.related_model
            self.source_model = item_model.source.field.related_model
            qs = qs.prefetch_related(
                    Prefetch(logs_name + '__item',
                        queryset=item_model.objects.only('source'),
                    ),
                    Prefetch(logs_name + '__item__source',
                        queryset=self.source_model.objects.only('name'),
                    )
                )
        return qs

    def dict_to_html(self, dt):
        return format_html_join('\n', "<li><b>{}:</b> {}</li>", ((key, val) for key, val in dt.items()))

    def crawl_stats(self, obj):
        return self.dict_to_html(obj.stats)

    def num_items(self, obj):
        return sum([getattr(obj, log_name).count() for log_name in self.LOGS_NAMES])

    def status_stats(self, obj):
        dt = {}
        for log in self.get_logs(obj):
            status = log.status_str()
            if status in dt:
                dt[status] += 1
            else:
                dt[status] = 1
        return self.dict_to_html(dt)

    def get_logs(self, obj):
        logs = []
        for logs_name in self.LOGS_NAMES:
            logs += list(getattr(obj, logs_name).all())
        return logs

class BaseItemLogAdmin(ModelAdmin):
    list_display = ('id', 'crawl_run', 'item_link', 'spider', 'status_str', 'message', 'time_taken_in_sec', 'created_at')
    fields = (('crawl_run', 'item_link', 'spider'), ('status_str', 'msg'), ('created_at', 'updated_at'))
    readonly_fields = ('crawl_run', 'item_link', 'spider', 'status_str', 'msg', 'created_at', 'updated_at')
    search_fields = ('item__source__name', 'item__key')
    list_filter = ('status', 'item__source')
    list_per_page = 10

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).prefetch_related('crawl_run')

    def item_link(self, obj):
        url = reverse('admin:%s_%s_change' % (obj.item._meta.app_label, obj.item._meta.model_name), args=[obj.item.id])
        return format_html('<a target="_blank" href="%s">%s</a>' % (url, obj.item))
    item_link.allow_tags=True

    def message(self, obj):
        try:
            return format_html(obj.msg.replace('\n', '<br />'))
        except:
            return obj.msg

