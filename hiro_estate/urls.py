"""
URL configuration for hiro_estate project.
This module includes security-related URLs.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .security_views import csp_report_view, security_headers_test_view

urlpatterns = [
    # مسیرهای اصلی سیستم
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('properties/', include('properties.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('config/', include('config.urls')),
    
    # صفحات استاتیک
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    
    # مسیرهای مرتبط با امنیت
    path('security/csp-report/', csp_report_view, name='csp_report'),
]

# مسیرهای فقط محیط توسعه
if settings.DEBUG:
    urlpatterns += [
        path('security/test-headers/', security_headers_test_view, name='security_headers_test'),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
