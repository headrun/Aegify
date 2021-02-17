from crawl.api import views as api

from .serializers import *

class BrowseListCreateUpdateView(api.ListCreateUpdateView):
    serializer_class = BrowseListCreateSerializer

class BrowseDetailView(api.DetailView):
    serializer_class = BrowseDetailSerializer

class ListingTerminalListCreateUpdateView(api.ListCreateUpdateView):
    serializer_class = ListingTerminalListCreateSerializer

class ListingTerminalDetailView(api.DetailView):
    serializer_class = ListingTerminalDetailSerializer

class DetailTerminalListCreateUpdateView(api.ListCreateUpdateView):
    serializer_class = DetailTerminalListCreateSerializer

class DetailTerminalDetailView(api.DetailView):
    serializer_class = DetailTerminalDetailSerializer

