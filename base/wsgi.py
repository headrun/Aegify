"""
WSGI config for Tracking project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from .settings import DjangoUtil; DjangoUtil.init()

application = get_wsgi_application()
