from django.contrib import admin
from .models import Property, PropertyType, TransactionType, PropertyStatus, DocumentType, PropertyImage

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

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'title', 'is_default', 'order')

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_code', 'title', 'property_type', 'transaction_type', 'status', 'price', 'area', 'created_at')
    list_filter = ('property_type', 'transaction_type', 'status', 'year_built')
    search_fields = ('property_code', 'title', 'address', 'description')
    readonly_fields = ('property_code', 'created_at', 'updated_at', 'slug')
    inlines = [PropertyImageInline]
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
        ('تصویر اصلی', {
            'fields': ('image',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('slug', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'title', 'is_default', 'order', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('property__property_code', 'property__title', 'title')
    list_editable = ('is_default', 'order')
    ordering = ('property', 'order', '-created_at')
