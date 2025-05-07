from django.urls import path
from . import views

app_name = 'config'

urlpatterns = [
    path('settings/', views.system_config_view, name='system_config'),
    path('backup/', views.backup_view, name='backup'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/restore/', views.restore_backup, name='restore_backup'),
    path('backup/export/properties/', views.export_properties_excel, name='export_properties_excel'),
    path('backup/export/system/', views.export_data_excel, name='export_data_excel'),
]
