from django import forms
from .models import SystemConfig

class SystemConfigForm(forms.ModelForm):
    """فرم تنظیمات سیستم"""
    
    class Meta:
        model = SystemConfig
        fields = '__all__'
        widgets = {
            # تنظیمات عمومی
            'website_title': forms.TextInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'default_property_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            
            # تنظیمات ظاهری
            'primary_color': forms.Select(attrs={'class': 'form-select'}),
            'font_type': forms.Select(attrs={'class': 'form-select'}),
            'enable_dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # تنظیمات تماس
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            
            # تنظیمات شبکه‌های اجتماعی
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://instagram.com/...'}),
            'telegram_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://t.me/...'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': '+98...'}),
            
            # تنظیمات SEO
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'site_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'کلمات کلیدی را با کاما جدا کنید'}),
            
            # پیکربندی‌های پیشرفته
            'enable_sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # تنظیمات ملک
            'price_unit': forms.Select(attrs={'class': 'form-select'}),
            'show_property_views': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_property_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_per_page': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 50}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اختیاری کردن فیلدهای تصویر برای جلوگیری از پاک شدن تصاویر موجود
        for field_name in ['favicon', 'logo', 'default_property_image']:
            self.fields[field_name].required = False
