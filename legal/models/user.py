from .base import *
from .detailterminal import DetailTerminal

class CrawlUser(BaseUser):
    source          = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='crawl_users')

    courses         = models.ManyToManyField(DetailTerminal, related_name='crawl_users')

    class Meta(BaseUser.Meta):
        unique_together = (('source', 'key'), )

class CrawlUserLog(BaseLog):
    crawl_run   = models.ForeignKey(CrawlRun, null=True, blank=True, on_delete=models.CASCADE, related_name='crawl_user_logs')
    item        = models.ForeignKey(CrawlUser, on_delete=models.CASCADE, related_name='logs')

