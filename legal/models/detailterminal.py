from .base import *

class DetailTerminal(ItemMixin, BaseBrowse):
    source          = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='detailterminal_items')
    key             = models.CharField(max_length=MAX_LENGTH_URL)

    last_scraped_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseItem.Meta):
        unique_together = (('source', 'key'), )

class DetailTerminalData(BaseData):
    item        = models.ForeignKey(DetailTerminal, on_delete=models.CASCADE, related_name='data_list')

    class Meta(BaseData.Meta):
        unique_together = (('item', 'name', 'order', 'hashkey'), )
        indexes = [
            models.Index(fields=('item', 'name', 'order', 'hashkey')),
        ]

class DetailTerminalLog(BaseLog):
    crawl_run   = models.ForeignKey(CrawlRun, null=True, blank=True, on_delete=models.CASCADE, related_name='item_logs')
    item        = models.ForeignKey(DetailTerminal, on_delete=models.CASCADE, related_name='logs')
