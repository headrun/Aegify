from crawl.models import *

class Source(BaseSource):
    class Meta(BaseSource.Meta):
        pass

class CrawlRun(BaseCrawlRun):
    source  = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='crawl_runs')
    is_logged =  models.BooleanField(default=False)
    logged_at = models.DateTimeField(null=True, blank=True)
    class Meta(BaseCrawlRun.Meta):
        pass

class ItemMixin:
    @classmethod
    def api_name(self):
        return self._meta.model_name
