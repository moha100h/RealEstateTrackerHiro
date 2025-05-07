"""
ASGI config for hiro_estate project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiro_estate.settings')

application = get_asgi_application()
