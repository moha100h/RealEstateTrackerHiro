from django.contrib import admin
from .models import SystemConfig, BackupRecord

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('website_title', 'font_type')
    fieldsets = (
        ('تنظیمات عمومی', {
            'fields': ('website_title', 'font_type')
        }),
        ('تصاویر', {
            'fields': ('logo', 'default_property_image')
        }),
    )

@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'created_at', 'created_by', 'file_size')
    readonly_fields = ('file_name', 'created_at', 'created_by', 'file_size')
    list_filter = ('created_at', 'created_by')
    search_fields = ('file_name',)
    
    def has_add_permission(self, request):
        return False
