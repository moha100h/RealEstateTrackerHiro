import django_filters
from django import forms
from .models import Property, PropertyType, TransactionType, PropertyStatus

class PropertyFilter(django_filters.FilterSet):
    """فیلتر پیشرفته برای جستجوی املاک"""
    property_code = django_filters.CharFilter(lookup_expr='icontains', label='کد ملک')
    address = django_filters.CharFilter(lookup_expr='icontains', label='آدرس')
    
    min_area = django_filters.NumberFilter(field_name='area', lookup_expr='gte', label='حداقل متراژ')
    max_area = django_filters.NumberFilter(field_name='area', lookup_expr='lte', label='حداکثر متراژ')
    
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='حداقل قیمت')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='حداکثر قیمت')
    
    min_year = django_filters.NumberFilter(field_name='year_built', lookup_expr='gte', label='از سال')
    max_year = django_filters.NumberFilter(field_name='year_built', lookup_expr='lte', label='تا سال')
    
    transaction_type = django_filters.ModelMultipleChoiceFilter(
        queryset=TransactionType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='نوع معامله'
    )
    
    status = django_filters.ModelMultipleChoiceFilter(
        queryset=PropertyStatus.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='وضعیت'
    )
    
    property_type = django_filters.ModelMultipleChoiceFilter(
        queryset=PropertyType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='نوع ملک'
    )
    
    class Meta:
        model = Property
        fields = [
            'property_code', 'address', 'property_type', 
            'transaction_type', 'status', 'year_built'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ به فیلترها
        for field_name, field in self.form.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
