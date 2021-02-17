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
from django.urls import path
from django.conf.urls import include

from ..settings import DjangoUtil;
settings = DjangoUtil.settings()

def get_urlpatterns(api_prefix=''):
    patterns = [
        path('oauth/', include('oauth2_provider.urls')),
    ]

    for app in settings.API_APP_LIST:
        try:
            patterns.append(
                path(api_prefix, include(app + '.api.urls'))
            )
        except ModuleNotFoundError:
            pass
    return patterns

urlpatterns = get_urlpatterns()
