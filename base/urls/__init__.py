"""Tracking URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.urls import path
from django.conf.urls import include, static
from django.http import HttpResponse
from django.contrib import admin

from ..utils import import_module_var
from ..settings import DjangoUtil;
settings = DjangoUtil.settings()

from ..views import home

from sites import INCLUDE_UPLOAD_URL

def report_view(request):
    try:
       f = open("/tmp/report.html",'r')
       temp = ''.join(f.readlines())
    except:
        temp = 'need to generate report'
    return HttpResponse(temp)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('report/', report_view),
    path('', home),
]

if os.environ.get('SITE') in INCLUDE_UPLOAD_URL:
	urlpatterns+=[(path('upload/', include('ecommerce.search.urls')))]

for app in settings.APP_LIST:
    prefix = import_module_var(app + '.URL_PREFIX', app)
    try:
        if prefix:
            prefix += '/'
        urlpatterns.append(
            path(prefix, include(app + '.urls'))
        )
    except ImportError:
        pass

from . import api
urlpatterns += api.get_urlpatterns('api/')

if settings.DEBUG:
    urlpatterns += static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
