"""
WSGI config for hiro_estate project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiro_estate.settings')

application = get_wsgi_application()
