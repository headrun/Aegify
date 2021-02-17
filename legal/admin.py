from django.contrib.admin import site, ModelAdmin

from crawl.admin import *

from .models import *

from .api.views import BrowseDetailView, ListingTerminalDetailView, \
                        DetailTerminalDetailView

site.register(Source, BaseSourceAdmin)

@register(CrawlRun)
class CrawlRunAdmin(BaseCrawlRunAdmin):
    LOGS_NAMES = BaseCrawlRunAdmin.LOGS_NAMES + ('listingterminal_logs', 'crawl_user_logs', )

class BrowseLogInline(BaseItemLogInline):
    model = BrowseLog

@register(Browse)
class BrowseAdmin(BaseBrowseAdmin):
    api_view = BrowseDetailView

    inlines = [
        BrowseLogInline
    ]

@register(BrowseLog)
class BrowseLogAdmin(BaseItemLogAdmin):
    pass

class ListingTerminalDataInline(BaseItemDataInline):
    model = ListingTerminalData

class ListingTerminalLogInline(BaseItemLogInline):
    model = ListingTerminalLog

@register(ListingTerminal)
class ListingTerminalAdmin(BaseItemAdmin):
    api_view = ListingTerminalDetailView

    inlines = [
        ListingTerminalDataInline,
        ListingTerminalLogInline
    ]

@register(ListingTerminalLog)
class ListingTerminalLogAdmin(BaseItemLogAdmin):
    pass

class DetailTerminalDataInline(BaseItemDataInline):
    model = DetailTerminalData

class DetailTerminalLogInline(BaseItemLogInline):
    model = DetailTerminalLog

@register(DetailTerminal)
class DetailTerminalAdmin(BaseItemAdmin):
    list_display = BaseItemAdmin.list_display + ('updated_at', 'last_scraped_at',)

    api_view = DetailTerminalDetailView

    inlines = [
        DetailTerminalDataInline,
        DetailTerminalLogInline
    ]

@register(DetailTerminalLog)
class DetailTerminalLogAdmin(BaseItemLogAdmin):
    pass

