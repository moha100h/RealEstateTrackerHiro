"""
تنظیمات پروژه هیرو املاک
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# در محیط تولید، میزبان‌های مجاز را محدود کنید
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,.replit.app,.replit.dev,.repl.co').split(',')

# CSRF settings for Replit
CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.dev',
    'https://*.replit.app',
    'https://*.repl.co',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party apps
    'django_filters',
    'django_jalali',
    
    # Custom apps
    'properties.apps.PropertiesConfig',
    'accounts.apps.AccountsConfig',
    'dashboard.apps.DashboardConfig',
    'config.apps.ConfigConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # محافظت در برابر حملات HTTP
    'django.middleware.http.ConditionalGetMiddleware',
    # میدل‌ویرهای سفارشی امنیتی
    'accounts.middleware.RateLimitMiddleware',
    'accounts.middleware.AccountLockoutMiddleware',
]

# حداکثر تعداد درخواست‌های مجاز 
# معمولا از سیستم‌های حرفه‌ای محدودیت نرخ مانند nginx استفاده می‌کنیم
# ولی این تنظیمات برای محافظت اولیه مناسب است
RATE_LIMIT_MIDDLEWARE = {
    'WINDOW_SIZE': 60 * 15,  # در هر 15 دقیقه
    'MAX_REQUESTS': 300,     # حداکثر 300 درخواست مجاز
    'EXEMPT_PATHS': ['/static/', '/media/'],
}

# تنظیمات امنیتی
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 سال
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# در محیط توسعه این تنظیمات False و در محیط تولید True باشند
USE_HTTPS = os.environ.get('USE_HTTPS', 'False') == 'True'
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_SSL_REDIRECT = USE_HTTPS

# محافظت از حملات SQL Injection
DATABASES_DEFAULT_CONN_MAX_AGE = 600  # 10 دقیقه
CONN_MAX_AGE = int(os.environ.get('CONN_MAX_AGE', DATABASES_DEFAULT_CONN_MAX_AGE))

# محافظت از سشن‌ها
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600  # 2 هفته
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

ROOT_URLCONF = 'hiro_estate.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.system_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'hiro_estate.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

import os

# Use PostgreSQL database for production or if DATABASE_URL is provided
if os.environ.get('DATABASE_URL'):
    # Parse the DATABASE_URL
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
else:
    # Use SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

# سیاست‌های امنیتی رمز عبور
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,  # طول حداقل رمز عبور (قوی)
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        'OPTIONS': {
            'password_list_path': None,  # استفاده از لیست پیش‌فرض رمزهای رایج
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# تنظیمات قفل کردن حساب کاربری بعد از تلاش‌های ناموفق
ACCOUNT_LOCKOUT_ATTEMPTS = 5  # تعداد تلاش‌های ناموفق قبل از قفل شدن
ACCOUNT_LOCKOUT_TIME = 30 * 60  # مدت زمان قفل شدن (30 دقیقه)

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fa-ir'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login redirect
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'home'

# Custom user model
# AUTH_USER_MODEL = 'accounts.User'

# تنظیمات امنیتی جامع برای حفاظت از سیستم
# -------------------------------------------------

# تنظیمات امنیتی سشن‌ها
SESSION_COOKIE_SECURE = True  # فقط در HTTPS ارسال شود
SESSION_COOKIE_HTTPONLY = True  # جلوگیری از دسترسی JavaScript به کوکی‌ها
SESSION_COOKIE_SAMESITE = 'Lax'  # محافظت در برابر حملات CSRF
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # خروج کاربر با بستن مرورگر
SESSION_COOKIE_AGE = 3600  # منقضی شدن سشن بعد از یک ساعت (تنظیم بر حسب ثانیه)

# CSRF configuration (محافظت در برابر حملات جعل درخواست)
CSRF_COOKIE_HTTPONLY = True  # محافظت از توکن CSRF در برابر دسترسی JavaScript
CSRF_USE_SESSIONS = True  # ذخیره توکن CSRF در سشن به جای کوکی برای امنیت بیشتر
CSRF_COOKIE_SAMESITE = 'Lax'  # محافظت در برابر حملات CSRF
CSRF_COOKIE_SECURE = True  # فقط در HTTPS ارسال شود
CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.app', 
    'http://localhost:5000', 
    'http://*.replit.dev',
    'https://*.spock.replit.dev',
    'https://*.id.repl.co',
    'https://*.repl.co'
]
# برای مدیریت بهتر خطاهای CSRF
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# HTTP Strict Transport Security (HSTS)
# مجبور کردن مرورگر به استفاده از HTTPS برای ارتباطات آینده
SECURE_HSTS_SECONDS = 31536000  # یک سال
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # شامل زیردامنه‌ها هم بشود
SECURE_HSTS_PRELOAD = True  # پشتیبانی از لیست preload مرورگرها

# Content Security Policy (CSP) 
# محدود کردن منابع مجاز برای بارگذاری محتوا
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'www.google-analytics.com', 'tagmanager.google.com')
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'fonts.googleapis.com')
CSP_FONT_SRC = ("'self'", 'fonts.gstatic.com', 'cdn.jsdelivr.net')
CSP_IMG_SRC = ("'self'", 'data:', 'www.google-analytics.com', 'stats.g.doubleclick.net')
CSP_CONNECT_SRC = ("'self'", 'www.google-analytics.com')
CSP_INCLUDE_NONCE_IN_CSP = True  # استفاده از nonce برای اسکریپت‌های پویا
CSP_FRAME_ANCESTORS = ("'self'",)  # محافظت در برابر حملات Clickjacking
CSP_REPORT_URI = '/security/csp-report/'  # آدرس گزارش تخلفات CSP

# X-Content-Type-Options
# جلوگیری از تشخیص نوع فایل توسط مرورگر (MIME sniffing)
SECURE_CONTENT_TYPE_NOSNIFF = True

# X-XSS-Protection
# محافظت داخلی مرورگر در برابر حملات XSS
SECURE_BROWSER_XSS_FILTER = True
X_XSS_PROTECTION = "1; mode=block"

# X-Frame-Options
# محافظت در برابر حملات Clickjacking
X_FRAME_OPTIONS = "SAMEORIGIN"

# Content-Security-Policy-Report-Only
# گزارش تخلفات بدون مسدود کردن محتوا (برای تست‌های اولیه)
# CSP_REPORT_ONLY = True  # در محیط توسعه فعال شود

# محدودیت نوع فایل‌های آپلودی مجاز
ALLOWED_UPLOAD_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',  # تصاویر
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # اسناد
    '.zip', '.rar',  # فایل‌های فشرده
]
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 مگابایت
