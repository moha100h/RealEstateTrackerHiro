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
]

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

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

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

# CSRF configuration
CSRF_COOKIE_HTTPONLY = True  # محافظت از توکن CSRF در برابر دسترسی JavaScript
CSRF_USE_SESSIONS = True  # ذخیره توکن CSRF در سشن به جای کوکی برای امنیت بیشتر
CSRF_COOKIE_SAMESITE = 'Lax'  # محافظت در برابر حملات CSRF
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
