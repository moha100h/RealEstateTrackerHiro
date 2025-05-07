from django import forms
from .models import SystemConfig

class SystemConfigForm(forms.ModelForm):
    """فرم تنظیمات سیستم"""
    
    class Meta:
        model = SystemConfig
        fields = ['website_title', 'logo', 'default_property_image', 'font_type']
        widgets = {
            'website_title': forms.TextInput(attrs={'class': 'form-control'}),
            'font_type': forms.Select(attrs={'class': 'form-select'}),
        }
