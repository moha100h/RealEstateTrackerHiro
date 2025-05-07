from django.db import models
from django.conf import settings
import os

class SystemConfig(models.Model):
    """تنظیمات سیستم"""
    website_title = models.CharField(max_length=100, default='سیستم هوشمند مدیریت املاک هیرو', verbose_name='عنوان وب‌سایت')
    logo = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='لوگو')
    default_property_image = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='تصویر پیش‌فرض املاک')
    font_type = models.CharField(
        max_length=20, 
        choices=[('vazir', 'فونت وزیر'), ('iransans', 'فونت ایران سنس')],
        default='vazir',
        verbose_name='نوع فونت'
    )
    
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
