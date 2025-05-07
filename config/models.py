from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
import os

class SystemConfig(models.Model):
    """تنظیمات سیستم"""
    # تنظیمات عمومی
    website_title = models.CharField(max_length=100, default='سیستم هوشمند مدیریت املاک هیرو', verbose_name='عنوان وب‌سایت')
    favicon = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='آیکون سایت')
    logo = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='لوگو')
    default_property_image = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='تصویر پیش‌فرض املاک')
    
    # تنظیمات ظاهری
    PRIMARY_COLORS = [
        ('blue', 'آبی'),
        ('green', 'سبز'), 
        ('red', 'قرمز'),
        ('purple', 'بنفش'),
        ('orange', 'نارنجی'),
        ('teal', 'فیروزه‌ای'),
    ]
    
    primary_color = models.CharField(
        max_length=20,
        choices=PRIMARY_COLORS,
        default='blue',
        verbose_name='رنگ اصلی سیستم'
    )
    
    font_type = models.CharField(
        max_length=20, 
        choices=[('vazir', 'فونت وزیر'), ('iransans', 'فونت ایران سنس'), ('sahel', 'فونت ساحل')],
        default='vazir',
        verbose_name='نوع فونت'
    )
    
    enable_dark_mode = models.BooleanField(default=False, verbose_name='فعال‌سازی حالت تاریک')
    
    # تنظیمات تماس
    company_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام شرکت/آژانس')
    company_address = models.TextField(blank=True, null=True, verbose_name='آدرس دفتر')
    company_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='شماره تماس')
    company_email = models.EmailField(blank=True, null=True, verbose_name='ایمیل تماس')
    
    # تنظیمات شبکه‌های اجتماعی
    instagram_url = models.URLField(blank=True, null=True, verbose_name='آدرس اینستاگرام')
    telegram_url = models.URLField(blank=True, null=True, verbose_name='آدرس تلگرام')
    whatsapp_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        verbose_name='شماره واتس‌اپ'
    )
    
    # تنظیمات SEO
    site_description = models.TextField(blank=True, null=True, verbose_name='توضیحات متا')
    site_keywords = models.TextField(blank=True, null=True, verbose_name='کلمات کلیدی')
    
    # پیکربندی‌های پیشرفته
    enable_sms_notifications = models.BooleanField(default=False, verbose_name='فعال‌سازی اطلاع‌رسانی پیامکی')
    maintenance_mode = models.BooleanField(default=False, verbose_name='حالت تعمیر و نگهداری')
    maintenance_message = models.TextField(blank=True, null=True, verbose_name='پیام حالت تعمیر و نگهداری')
    
    # تنظیمات ملک
    price_unit = models.CharField(
        max_length=20,
        choices=[('toman', 'تومان'), ('rial', 'ریال'), ('dollar', 'دلار')],
        default='toman',
        verbose_name='واحد قیمت'
    )
    
    show_property_views = models.BooleanField(default=True, verbose_name='نمایش تعداد بازدیدها')
    enable_property_comments = models.BooleanField(default=False, verbose_name='فعال‌سازی نظرات')
    property_per_page = models.PositiveIntegerField(default=10, verbose_name='تعداد املاک در هر صفحه')
    
    class Meta:
        verbose_name = 'تنظیمات سیستم'
        verbose_name_plural = 'تنظیمات سیستم'
    
    def __str__(self):
        return self.website_title
    
    @staticmethod
    def get_config():
        """دریافت تنظیمات سیستم یا ایجاد موارد پیش‌فرض"""
        config = SystemConfig.objects.first()
        if not config:
            config = SystemConfig.objects.create()
        return config

class BackupRecord(models.Model):
    """ثبت تاریخچه پشتیبان‌گیری"""
    file_name = models.CharField(max_length=255, verbose_name='نام فایل')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='ایجاد توسط')
    file_size = models.PositiveIntegerField(default=0, verbose_name='حجم فایل (بایت)')
    
    class Meta:
        verbose_name = 'سابقه پشتیبان‌گیری'
        verbose_name_plural = 'سوابق پشتیبان‌گیری'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_file_size_display(self):
        """نمایش حجم فایل به صورت خوانا"""
        if self.file_size < 1024:
            return f"{self.file_size} بایت"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} کیلوبایت"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} مگابایت"
