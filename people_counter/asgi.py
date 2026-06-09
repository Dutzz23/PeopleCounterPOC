"""ASGI config for people_counter project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "people_counter.settings")

application = get_asgi_application()
