from django.contrib import admin
from .models import Property, PropertyType, TransactionType, PropertyStatus, DocumentType

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PropertyStatus)
class PropertyStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    
@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_code', 'title', 'property_type', 'transaction_type', 'status', 'price', 'area', 'created_at')
    list_filter = ('property_type', 'transaction_type', 'status', 'year_built')
    search_fields = ('property_code', 'title', 'address', 'description')
    readonly_fields = ('property_code', 'created_at', 'updated_at', 'slug')
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('property_code', 'title', 'address', 'description')
        }),
        ('مشخصات فنی', {
            'fields': ('area', 'price', 'year_built', 'rooms')
        }),
        ('دسته بندی', {
            'fields': ('property_type', 'transaction_type', 'status', 'document_type')
        }),
        ('تصویر', {
            'fields': ('image',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('slug', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
