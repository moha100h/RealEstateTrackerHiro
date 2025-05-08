from django import forms
from .models import SystemConfig

class SystemConfigForm(forms.ModelForm):
    """فرم پیشرفته تنظیمات سیستم"""
    
    class Meta:
        model = SystemConfig
        fields = '__all__'
        widgets = {
            # تنظیمات عمومی
            'website_title': forms.TextInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo_footer': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'default_property_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # تنظیمات ظاهری
            'primary_color': forms.Select(attrs={'class': 'form-select'}),
            'secondary_color': forms.Select(attrs={'class': 'form-select'}),
            'font_type': forms.Select(attrs={'class': 'form-select'}),
            'navbar_style': forms.Select(attrs={'class': 'form-select'}),
            'footer_style': forms.Select(attrs={'class': 'form-select'}),
            'layout_style': forms.Select(attrs={'class': 'form-select'}),
            'enable_dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_rtl_switch': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_animations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_back_to_top': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # تنظیمات تماس
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'company_fax': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'support_email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'business_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'google_maps_embed': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'dir': 'ltr'}),
            
            # تنظیمات شبکه‌های اجتماعی
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://instagram.com/...'}),
            'telegram_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://t.me/...'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': '+98...'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://linkedin.com/in/...'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://twitter.com/...'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://facebook.com/...'}),
            'aparat_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://aparat.com/...'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://youtube.com/...'}),
            
            # تنظیمات SEO
            'site_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'site_keywords': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'کلمات کلیدی را با کاما جدا کنید'}),
            'enable_structured_data': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'google_analytics_id': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'UA-123456789-1 یا G-XXXXXXXXXX'}),
            'google_tag_manager_id': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'GTM-XXXXXXX'}),
            'google_search_console': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'canonical_domain': forms.URLInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'https://example.com'}),
            
            # پیکربندی‌های پیشرفته
            'enable_sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_api_key': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'sms_line_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'enable_email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': 'smtp.example.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': '587'}),
            'smtp_username': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'smtp_password': forms.PasswordInput(attrs={'class': 'form-control', 'dir': 'ltr', 'autocomplete': 'new-password'}),
            'use_ssl_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cache_timeout': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 86400}),
            'enable_http2_push': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_csp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_hsts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # تنظیمات ملک
            'price_unit': forms.Select(attrs={'class': 'form-select'}),
            'area_unit': forms.Select(attrs={'class': 'form-select'}),
            'show_price_format': forms.Select(attrs={'class': 'form-select'}),
            'show_property_views': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_property_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_per_page': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 50}),
            'enable_property_rating': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_favorites': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_compare': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_property_sharing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_print_listing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_pdf_export': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_card_style': forms.Select(attrs={'class': 'form-select'}),
            'default_sort_properties': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اختیاری کردن تمام فیلدها به جز چکباکس‌ها
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.required = False
                
        # افزودن کلاس‌های CSS اضافی برای ورودی‌های حساس
        sensitive_fields = ['sms_api_key', 'smtp_password', 'google_analytics_id', 'google_tag_manager_id']
        for field_name in sensitive_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'autocomplete': 'off', 'class': 'form-control sensitive-field'})
                
        # کلاس‌های اضافی برای بهبود UX
        for field_name in self.fields:
            widget = self.fields[field_name].widget
            if isinstance(widget, forms.Select):
                widget.attrs.update({'data-live-search': 'true'})
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({'data-autoresize': 'true'})
                
        # گروه‌بندی فیلدها برای استفاده در قالب
        self.field_groups = {
            'general': ['website_title', 'favicon', 'logo', 'logo_footer', 'default_property_image', 'footer_text'],
            'appearance': ['primary_color', 'secondary_color', 'font_type', 'navbar_style', 'footer_style', 'layout_style', 
                          'enable_dark_mode', 'enable_rtl_switch', 'enable_animations', 'enable_back_to_top'],
            'contact': ['company_name', 'company_address', 'company_phone', 'company_fax', 'company_email', 
                       'support_email', 'business_hours', 'google_maps_embed'],
            'social': ['instagram_url', 'telegram_url', 'whatsapp_number', 'linkedin_url', 'twitter_url', 
                      'facebook_url', 'aparat_url', 'youtube_url'],
            'seo': ['site_description', 'site_keywords', 'enable_structured_data', 'google_analytics_id', 
                   'google_tag_manager_id', 'google_search_console', 'canonical_domain'],
            'advanced': ['enable_sms_notifications', 'sms_api_key', 'sms_line_number', 'enable_email_notifications', 
                        'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'use_ssl_email', 
                        'maintenance_mode', 'maintenance_message', 'cache_timeout', 'enable_http2_push', 
                        'enable_csp', 'enable_hsts'],
            'property': ['price_unit', 'area_unit', 'show_price_format', 'show_property_views', 'enable_property_comments', 
                        'property_per_page', 'enable_property_rating', 'enable_favorites', 'enable_compare', 
                        'enable_property_sharing', 'enable_print_listing', 'enable_pdf_export', 
                        'property_card_style', 'default_sort_properties']
        }
