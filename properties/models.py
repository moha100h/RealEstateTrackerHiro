"""
مدل های مرتبط با املاک
"""
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid
import os
import imghdr
import mimetypes
from django.utils import timezone
from django_jalali.db import models as jmodels

def validate_file_extension(value):
    """
    تابع تأیید پسوند فایل آپلود شده برای جلوگیری از آپلود فایل‌های مخرب
    """
    ext = os.path.splitext(value.name)[1]
    valid_extensions = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar'])
    if ext.lower() not in valid_extensions:
        allowed_extensions_str = '، '.join(valid_extensions)
        raise ValidationError(f'پسوند فایل غیرمجاز است. پسوندهای مجاز: {allowed_extensions_str}')

def validate_file_size(value):
    """
    تابع تأیید حجم فایل آپلود شده برای جلوگیری از حملات DoS
    """
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)  # 5 مگابایت پیش‌فرض
    if value.size > max_size:
        raise ValidationError(f'حجم فایل بیشتر از حد مجاز ({max_size/1024/1024:.1f} مگابایت) است.')

def validate_image_file(value):
    """
    تأیید این که فایل آپلود شده واقعاً یک تصویر معتبر است
    """
    # برای تصاویر، از imghdr استفاده می‌کنیم که در کتابخانه استاندارد پایتون وجود دارد
    file_content = value.read()
    value.seek(0)  # بازگشت به ابتدای فایل
    
    image_format = imghdr.what(None, file_content)
    if image_format not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
        raise ValidationError('فایل آپلود شده یک تصویر معتبر نیست.')

def secure_upload_validator(value):
    """
    اعمال ولیدیتورهای امنیتی بر روی فایل آپلود شده
    """
    validate_file_extension(value)
    validate_file_size(value)
    
    # اگر فایل تصویر است، بررسی محتوای آن
    ext = os.path.splitext(value.name)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        validate_image_file(value)

class PropertyType(models.Model):
    """
    نوع ملک (مسکونی، تجاری و غیره)
    """
    name = models.CharField(max_length=100, verbose_name="نام")
    
    class Meta:
        verbose_name = "نوع ملک"
        verbose_name_plural = "انواع ملک"
        
    def __str__(self):
        return self.name

class TransactionType(models.Model):
    """
    نوع معامله (فروش، اجاره، رهن)
    """
    name = models.CharField(max_length=100, verbose_name="نام")
    
    class Meta:
        verbose_name = "نوع معامله"
        verbose_name_plural = "انواع معامله"
        
    def __str__(self):
        return self.name

class PropertyStatus(models.Model):
    """
    وضعیت ملک (موجود، فروخته شده، اجاره داده شده، رزرو شده و غیره)
    """
    name = models.CharField(max_length=100, verbose_name="نام")
    
    class Meta:
        verbose_name = "وضعیت ملک"
        verbose_name_plural = "وضعیت های ملک"
        
    def __str__(self):
        return self.name

class DocumentType(models.Model):
    """
    نوع سند (تک برگ، شش دانگ، قولنامه ای، وکالتی و غیره)
    """
    name = models.CharField(max_length=100, verbose_name="نام")
    
    class Meta:
        verbose_name = "نوع سند"
        verbose_name_plural = "انواع سند"
        
    def __str__(self):
        return self.name

class Property(models.Model):
    """
    مدل اصلی املاک
    """
    property_code = models.CharField(max_length=10, unique=True, editable=False, verbose_name="کد ملک")
    title = models.CharField(max_length=255, verbose_name="عنوان")
    address = models.TextField(verbose_name="آدرس کامل")
    area = models.PositiveIntegerField(verbose_name="متراژ (متر مربع)")
    price = models.BigIntegerField(verbose_name="قیمت")
    year_built = models.PositiveIntegerField(verbose_name="سال ساخت")
    property_type = models.ForeignKey(PropertyType, on_delete=models.CASCADE, verbose_name="نوع ملک")
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.CASCADE, verbose_name="نوع معامله")
    status = models.ForeignKey(PropertyStatus, on_delete=models.CASCADE, verbose_name="وضعیت")
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="نوع سند")
    rooms = models.PositiveSmallIntegerField(verbose_name="تعداد اتاق")
    description = models.TextField(verbose_name="توضیحات")
    image = models.ImageField(
        upload_to='properties/', 
        blank=True, 
        null=True, 
        verbose_name="تصویر اصلی",
        validators=[secure_upload_validator]
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    slug = models.SlugField(unique=True, blank=True, verbose_name="اسلاگ")
    
    class Meta:
        verbose_name = "ملک"
        verbose_name_plural = "املاک"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # ایجاد کد منحصر به فرد برای ملک
        if not self.property_code:
            self.property_code = f"P{str(uuid.uuid4().int)[:8]}"
        
        # ایجاد اسلاگ
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.property_code}")
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.property_code})"
        
    def get_additional_images(self):
        """دریافت لیست تصاویر اضافی ملک"""
        return self.images.all()


class PropertyImage(models.Model):
    """
    مدل تصاویر اضافی ملک برای گالری تصاویر
    """
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images', verbose_name="ملک")
    image = models.ImageField(
        upload_to='property_images/', 
        verbose_name="تصویر",
        validators=[secure_upload_validator]
    )
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="عنوان تصویر")
    is_default = models.BooleanField(default=False, verbose_name="تصویر پیش‌فرض")
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")
    
    class Meta:
        verbose_name = "تصویر ملک"
        verbose_name_plural = "تصاویر ملک"
        ordering = ['order', '-created_at']
        
    def __str__(self):
        return f"تصویر {self.property.property_code}"
