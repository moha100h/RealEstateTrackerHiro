from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator, EmailValidator, URLValidator
from django.core.exceptions import ValidationError
import os
import re

def validate_no_script(value):
    """
    اعتبارسنجی برای جلوگیری از ورود اسکریپت‌های مخرب
    """
    if re.search(r'<\s*script.*?>.*?<\s*/\s*script\s*>', value, re.IGNORECASE | re.DOTALL):
        raise ValidationError("محتوای وارد شده حاوی کدهای اسکریپت غیرمجاز است.")
    
    # تگ‌های خطرناک دیگر 
    dangerous_patterns = [
        r'<\s*iframe.*?>',
        r'javascript\s*:',
        r'on\w+\s*=',
        r'<\s*img.*?onerror.*?>',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
            raise ValidationError("محتوای وارد شده حاوی کدهای غیرمجاز است.")
    
    return value

def validate_file_path(value):
    """
    اعتبارسنجی برای جلوگیری از دستکاری مسیر فایل
    """
    if '..' in value or value.startswith('/'):
        raise ValidationError("مسیر فایل نامعتبر است. تلاش برای تغییر مسیر تشخیص داده شد.")
    return value

class SystemConfig(models.Model):
    """تنظیمات سیستم"""
    # تنظیمات عمومی
    website_title = models.CharField(
        max_length=100, 
        default='سیستم هوشمند مدیریت املاک هیرو', 
        validators=[MinLengthValidator(3), MaxLengthValidator(100), validate_no_script],
        verbose_name='عنوان وب‌سایت'
    )
    favicon = models.ImageField(
        upload_to='config/', 
        blank=True, 
        null=True, 
        verbose_name='آیکون سایت'
    )
    logo = models.ImageField(
        upload_to='config/', 
        blank=True, 
        null=True, 
        verbose_name='لوگو'
    )
    logo_footer = models.ImageField(
        upload_to='config/', 
        blank=True, 
        null=True, 
        verbose_name='لوگوی فوتر'
    )
    default_property_image = models.ImageField(
        upload_to='config/', 
        blank=True, 
        null=True, 
        verbose_name='تصویر پیش‌فرض املاک'
    )
    footer_text = models.TextField(
        blank=True,
        null=True,
        validators=[MaxLengthValidator(500), validate_no_script],
        verbose_name='متن فوتر سایت',
        help_text='توضیحات پایین صفحه که در همه صفحات نمایش داده می‌شود'
    )
    
    # تنظیمات ظاهری
    PRIMARY_COLORS = [
        ('blue', 'آبی'),
        ('green', 'سبز'), 
        ('red', 'قرمز'),
        ('purple', 'بنفش'),
        ('orange', 'نارنجی'),
        ('teal', 'فیروزه‌ای'),
        ('indigo', 'نیلی'),
        ('pink', 'صورتی'),
    ]
    
    NAVBAR_STYLES = [
        ('default', 'پیش‌فرض'),
        ('gradient', 'گرادیانت'),
        ('transparent', 'شفاف'),
        ('dark', 'تیره'),
        ('light', 'روشن'),
        ('colored', 'رنگی'),
    ]
    
    LAYOUT_STYLES = [
        ('default', 'پیش‌فرض'),
        ('boxed', 'جعبه‌ای'),
        ('fluid', 'کامل عرض'),
        ('compact', 'فشرده'),
    ]
    
    primary_color = models.CharField(
        max_length=20,
        choices=PRIMARY_COLORS,
        default='blue',
        verbose_name='رنگ اصلی سیستم'
    )
    
    secondary_color = models.CharField(
        max_length=20,
        choices=PRIMARY_COLORS,
        default='teal',
        verbose_name='رنگ ثانویه سیستم'
    )
    
    font_type = models.CharField(
        max_length=20, 
        choices=[('vazir', 'فونت وزیر'), ('iransans', 'فونت ایران سنس'), ('sahel', 'فونت ساحل'), ('estedad', 'فونت استعداد'), ('yekan', 'فونت یکان')],
        default='vazir',
        verbose_name='نوع فونت'
    )
    
    navbar_style = models.CharField(
        max_length=20,
        choices=NAVBAR_STYLES,
        default='default',
        verbose_name='سبک منوی اصلی'
    )
    
    footer_style = models.CharField(
        max_length=20,
        choices=[('default', 'پیش‌فرض'), ('simple', 'ساده'), ('dark', 'تیره'), ('colored', 'رنگی')],
        default='default',
        verbose_name='سبک فوتر'
    )
    
    layout_style = models.CharField(
        max_length=20,
        choices=LAYOUT_STYLES,
        default='default',
        verbose_name='نوع چیدمان صفحه'
    )
    
    enable_dark_mode = models.BooleanField(default=False, verbose_name='فعال‌سازی حالت تاریک')
    enable_rtl_switch = models.BooleanField(default=False, verbose_name='امکان تغییر جهت راست/چپ')
    enable_animations = models.BooleanField(default=True, verbose_name='فعال‌سازی انیمیشن‌ها')
    enable_back_to_top = models.BooleanField(default=True, verbose_name='دکمه بازگشت به بالا')
    
    # تنظیمات تماس
    company_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        validators=[MaxLengthValidator(100), validate_no_script],
        verbose_name='نام شرکت/آژانس'
    )
    company_address = models.TextField(
        blank=True, 
        null=True,
        validators=[MaxLengthValidator(500), validate_no_script],
        verbose_name='آدرس دفتر'
    )
    company_phone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^\+?[0-9]{8,15}$', message='شماره تلفن باید فقط شامل اعداد و حداکثر یک علامت + باشد')],
        verbose_name='شماره تماس'
    )
    company_fax = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^\+?[0-9]{8,15}$', message='شماره فکس باید فقط شامل اعداد و حداکثر یک علامت + باشد')],
        verbose_name='شماره فکس'
    )
    company_email = models.EmailField(
        blank=True, 
        null=True,
        validators=[EmailValidator(message='ایمیل وارد شده معتبر نیست')],
        verbose_name='ایمیل تماس'
    )
    support_email = models.EmailField(
        blank=True, 
        null=True,
        validators=[EmailValidator(message='ایمیل وارد شده معتبر نیست')],
        verbose_name='ایمیل پشتیبانی'
    )
    business_hours = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(100), validate_no_script],
        verbose_name='ساعات کاری',
        help_text='مثال: شنبه تا چهارشنبه 9 الی 17'
    )
    google_maps_embed = models.TextField(
        blank=True,
        null=True,
        verbose_name='کد جاسازی نقشه گوگل',
        help_text='کد iframe گوگل مپ برای نمایش موقعیت دفتر'
    )
    
    # تنظیمات شبکه‌های اجتماعی
    instagram_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس اینستاگرام'
    )
    telegram_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس تلگرام'
    )
    whatsapp_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        validators=[RegexValidator(regex=r'^\+?[0-9]{9,15}$', message='شماره واتس‌اپ باید فقط شامل اعداد و حداکثر یک علامت + باشد')],
        verbose_name='شماره واتس‌اپ'
    )
    linkedin_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس لینکدین'
    )
    twitter_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس توییتر'
    )
    facebook_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس فیسبوک'
    )
    aparat_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس آپارات'
    )
    youtube_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator(message='آدرس وارد شده معتبر نیست')],
        verbose_name='آدرس یوتیوب'
    )
    
    # تنظیمات SEO
    site_description = models.TextField(
        blank=True, 
        null=True, 
        validators=[MaxLengthValidator(1000), validate_no_script],
        verbose_name='توضیحات متا'
    )
    site_keywords = models.TextField(
        blank=True, 
        null=True, 
        validators=[MaxLengthValidator(500), validate_no_script],
        verbose_name='کلمات کلیدی'
    )
    enable_structured_data = models.BooleanField(
        default=True, 
        verbose_name='فعال‌سازی داده ساختاریافته',
        help_text='بهینه‌سازی برای نمایش بهتر در نتایج گوگل'
    )
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='شناسه گوگل آنالیتیکس',
        help_text='مثال: UA-123456789-1 یا G-XXXXXXXXXX'
    )
    google_tag_manager_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='شناسه گوگل تگ منیجر',
        help_text='مثال: GTM-XXXXXXX'
    )
    google_search_console = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='کد تأیید گوگل سرچ کنسول',
        help_text='کد تأیید مالکیت سایت در گوگل سرچ کنسول'
    )
    canonical_domain = models.URLField(
        blank=True,
        null=True,
        verbose_name='دامنه اصلی سایت',
        help_text='برای تنظیم لینک canonical (مثال: https://example.com)'
    )
    
    # پیکربندی‌های پیشرفته
    enable_sms_notifications = models.BooleanField(default=False, verbose_name='فعال‌سازی اطلاع‌رسانی پیامکی')
    sms_api_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='کلید API پیامک',
        help_text='کلید API سرویس پیامک'
    )
    sms_line_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='شماره خط پیامکی',
        help_text='شماره خط ارسال پیامک'
    )
    enable_email_notifications = models.BooleanField(default=False, verbose_name='فعال‌سازی اطلاع‌رسانی ایمیلی')
    smtp_host = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='هاست SMTP',
        help_text='آدرس سرور SMTP برای ارسال ایمیل'
    )
    smtp_port = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='پورت SMTP',
        help_text='معمولاً 587 یا 465'
    )
    smtp_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='نام کاربری SMTP'
    )
    smtp_password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='رمز عبور SMTP'
    )
    use_ssl_email = models.BooleanField(default=True, verbose_name='استفاده از SSL برای ایمیل')
    maintenance_mode = models.BooleanField(default=False, verbose_name='حالت تعمیر و نگهداری')
    maintenance_message = models.TextField(
        blank=True, 
        null=True, 
        validators=[MaxLengthValidator(1000), validate_no_script],
        verbose_name='پیام حالت تعمیر و نگهداری'
    )
    cache_timeout = models.PositiveIntegerField(
        default=3600,
        verbose_name='زمان کش (ثانیه)',
        help_text='مدت زمان ذخیره‌سازی کش صفحات (3600 = یک ساعت)'
    )
    enable_http2_push = models.BooleanField(
        default=False,
        verbose_name='فعال‌سازی HTTP/2 Push',
        help_text='بهبود سرعت بارگذاری صفحات'
    )
    enable_csp = models.BooleanField(
        default=True,
        verbose_name='فعال‌سازی Content Security Policy',
        help_text='افزایش امنیت با محدود کردن منابع مجاز'
    )
    enable_hsts = models.BooleanField(
        default=True,
        verbose_name='فعال‌سازی HSTS',
        help_text='اجبار اتصال HTTPS برای افزایش امنیت'
    )
    
    # تنظیمات ملک
    price_unit = models.CharField(
        max_length=20,
        choices=[('toman', 'تومان'), ('rial', 'ریال'), ('dollar', 'دلار'), ('euro', 'یورو'), ('dirham', 'درهم')],
        default='toman',
        verbose_name='واحد قیمت'
    )
    area_unit = models.CharField(
        max_length=20,
        choices=[('meter', 'متر مربع'), ('foot', 'فوت مربع')],
        default='meter',
        verbose_name='واحد متراژ'
    )
    show_price_format = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'معمولی (۱۰۰۰۰۰۰)'), 
            ('formatted', 'فرمت‌شده (۱,۰۰۰,۰۰۰)'), 
            ('abbreviated', 'خلاصه (۱ میلیون)'),
            ('text', 'متنی (یک میلیون تومان)')
        ],
        default='formatted',
        verbose_name='نحوه نمایش قیمت'
    )
    show_property_views = models.BooleanField(default=True, verbose_name='نمایش تعداد بازدیدها')
    enable_property_comments = models.BooleanField(default=False, verbose_name='فعال‌سازی نظرات')
    property_per_page = models.PositiveIntegerField(default=10, verbose_name='تعداد املاک در هر صفحه')
    enable_property_rating = models.BooleanField(default=False, verbose_name='فعال‌سازی امتیازدهی به املاک')
    enable_favorites = models.BooleanField(default=True, verbose_name='فعال‌سازی لیست علاقه‌مندی‌ها')
    enable_compare = models.BooleanField(default=True, verbose_name='فعال‌سازی مقایسه املاک')
    enable_property_sharing = models.BooleanField(default=True, verbose_name='فعال‌سازی اشتراک‌گذاری املاک')
    enable_print_listing = models.BooleanField(default=True, verbose_name='فعال‌سازی چاپ مشخصات ملک')
    enable_pdf_export = models.BooleanField(default=True, verbose_name='فعال‌سازی خروجی PDF')
    property_card_style = models.CharField(
        max_length=20,
        choices=[
            ('default', 'پیش‌فرض'), 
            ('compact', 'فشرده'), 
            ('grid', 'شبکه‌ای'),
            ('list', 'لیستی'),
            ('modern', 'مدرن')
        ],
        default='default',
        verbose_name='سبک کارت املاک'
    )
    default_sort_properties = models.CharField(
        max_length=20,
        choices=[
            ('newest', 'جدیدترین'), 
            ('price_low', 'ارزان‌ترین'), 
            ('price_high', 'گران‌ترین'),
            ('area_high', 'بزرگترین'),
            ('views', 'پربازدیدترین')
        ],
        default='newest',
        verbose_name='مرتب‌سازی پیش‌فرض املاک'
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
    file_name = models.CharField(
        max_length=255, 
        validators=[MaxLengthValidator(255), validate_no_script, validate_file_path],
        verbose_name='نام فایل'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='تاریخ ایجاد'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        verbose_name='ایجاد توسط'
    )
    file_size = models.PositiveIntegerField(
        default=0, 
        verbose_name='حجم فایل (بایت)'
    )
    
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
