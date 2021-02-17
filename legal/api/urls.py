from .views import *

version=1

views = [
    BrowseDetailView,
    BrowseListCreateUpdateView,

    ListingTerminalDetailView,
    ListingTerminalListCreateUpdateView,

    DetailTerminalDetailView,
    DetailTerminalListCreateUpdateView,
]

urlpatterns = []
[urlpatterns.extend(view.urlpatterns(version)) for view in views]

