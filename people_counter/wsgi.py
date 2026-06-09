"""WSGI config for people_counter project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "people_counter.settings")

application = get_wsgi_application()
