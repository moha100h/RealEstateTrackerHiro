from django.contrib import admin
from .models import SystemConfig, BackupRecord

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('website_title', 'font_type', 'show_property_contact_info')
    fieldsets = (
        ('تنظیمات عمومی', {
            'fields': ('website_title', 'font_type')
        }),
        ('تصاویر', {
            'fields': ('logo', 'default_property_image')
        }),
        ('تنظیمات اطلاعات تماس مشاور ملک', {
            'fields': (
                'show_property_contact_info',
                'property_contact_name',
                'property_contact_position',
                'property_contact_avatar',
                'property_contact_phone',
                'property_contact_mobile',
                'property_contact_email',
                'property_contact_whatsapp'
            ),
            'description': 'تنظیمات مربوط به نمایش اطلاعات تماس مشاور در صفحه جزئیات ملک'
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
