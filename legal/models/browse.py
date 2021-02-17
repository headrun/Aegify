from .base import *
from .detailterminal import DetailTerminal

class ListingTerminal(ItemMixin, BaseBrowse):
    source          = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='listingterminal_items')
    key             = models.CharField(max_length=MAX_LENGTH_URL)

    detail       = models.ForeignKey(DetailTerminal, null=True, blank=True, on_delete=models.CASCADE, related_name='listingterminal_items')
    #scholarship_browse  = models.ForeignKey(ScholarshipBrowse, null=True, blank=True, on_delete=models.CASCADE, related_name='listingterminal_items')

    class Meta(BaseItem.Meta):
        unique_together = (('source', 'key'), )
        verbose_name_plural = 'Listings'

class ListingTerminalData(BaseData):
    item        = models.ForeignKey(ListingTerminal, on_delete=models.CASCADE, related_name='data_list')

    class Meta(BaseData.Meta):
        unique_together = (('item', 'name', 'order', 'hashkey'), )
        indexes = [
            models.Index(fields=('item', 'name', 'order', 'hashkey')),
        ]

class ListingTerminalLog(BaseLog):
    crawl_run   = models.ForeignKey(CrawlRun, null=True, blank=True, on_delete=models.CASCADE, related_name='listingterminal_logs')
    item        = models.ForeignKey(ListingTerminal, on_delete=models.CASCADE, related_name='logs')

class Browse(ItemMixin, BaseBrowse):
    source          = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='browse_items')
    key             = models.CharField(max_length=MAX_LENGTH_URL)

    items           = models.ManyToManyField(ListingTerminal, related_name='browse_items')

    class Meta(BaseItem.Meta):
        unique_together = (('source', 'key'), )

class BrowseLog(BaseLog):
    crawl_run   = models.ForeignKey(CrawlRun, null=True, blank=True, on_delete=models.CASCADE, related_name='browse_logs')
    item        = models.ForeignKey(Browse, on_delete=models.CASCADE, related_name='logs')
