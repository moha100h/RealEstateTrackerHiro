<div dir="rtl">

# سیستم هوشمند مدیریت املاک هیرو

## راهنمای نصب و راه‌اندازی سیستم روی سرور Ubuntu

این راهنما شامل مراحل کامل نصب و پیکربندی "سیستم هوشمند مدیریت املاک هیرو" روی سرور Ubuntu 22.04 LTS است. این پیکربندی اجازه می‌دهد سیستم روی پورت 80 (بدون نیاز به وارد کردن شماره پورت در URL) در دسترس باشد.

### فهرست مطالب
1. [پیش‌نیازهای سرور](#پیش-نیازهای-سرور)
2. [نصب بسته‌های مورد نیاز](#نصب-بسته-های-مورد-نیاز)
3. [نصب و پیکربندی PostgreSQL](#نصب-و-پیکربندی-postgresql)
4. [آماده‌سازی پروژه](#آماده-سازی-پروژه)
5. [پیکربندی پروژه جنگو](#پیکربندی-پروژه-جنگو)
6. [نصب و پیکربندی Gunicorn](#نصب-و-پیکربندی-gunicorn)
7. [پیکربندی Nginx](#پیکربندی-nginx)
8. [پیکربندی SSL/TLS با Let's Encrypt](#پیکربندی-ssltls-با-lets-encrypt)
9. [راه‌اندازی سرویس سیستمی](#راه-اندازی-سرویس-سیستمی)
10. [ایجاد کاربر سوپر ادمین](#ایجاد-کاربر-سوپر-ادمین)
11. [تنظیمات فایروال](#تنظیمات-فایروال)
12. [پیکربندی پشتیبان‌گیری خودکار](#پیکربندی-پشتیبان-گیری-خودکار)

### پیش‌نیازهای سرور

- سرور Ubuntu 22.04 LTS با دسترسی root
- یک نام دامنه (اختیاری، اما برای SSL توصیه می‌شود)
- حداقل 1GB RAM و 20GB فضای دیسک

### نصب بسته‌های مورد نیاز

ابتدا سیستم را به‌روزرسانی کرده و بسته‌های مورد نیاز را نصب می‌کنیم:

```bash
# به‌روزرسانی سیستم
sudo apt update
sudo apt upgrade -y

# نصب بسته‌های ضروری
sudo apt install -y python3-pip python3-dev python3-venv libpq-dev postgresql postgresql-contrib nginx curl supervisor git

# نصب بسته‌های مورد نیاز برای PIL
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev
```

### نصب و پیکربندی PostgreSQL

```bash
# وارد شدن به محیط PostgreSQL
sudo -u postgres psql

# ایجاد کاربر و دیتابیس (در محیط psql)
CREATE DATABASE hiroestate;
CREATE USER hiroestate_user WITH PASSWORD 'رمز_عبور_قوی';
ALTER ROLE hiroestate_user SET client_encoding TO 'utf8';
ALTER ROLE hiroestate_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE hiroestate_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hiroestate TO hiroestate_user;
# برای خروج از محیط psql
\q
```

### آماده‌سازی پروژه

```bash
# ایجاد کاربر سیستمی برای اجرای برنامه (توصیه امنیتی)
sudo adduser --system --group hiroestate

# ایجاد دایرکتوری برای پروژه
sudo mkdir -p /var/www/hiroestate
sudo chown hiroestate:hiroestate /var/www/hiroestate

# انتقال کد پروژه به سرور
# فرض: کد پروژه روی لپ‌تاپ/کامپیوتر شخصی شماست و از طریق SCP منتقل می‌شود
# در کامپیوتر محلی خودتان این دستور را اجرا کنید:
# scp -r /path/to/your/hiroestate/* username@your_server_ip:/var/www/hiroestate/

# یا با استفاده از Git برای کلون کردن مخزن (اگر پروژه در مخزن گیت است)
cd /var/www/hiroestate
sudo -u hiroestate git clone https://your-repository-url.git .

# تنظیم مجوزهای دسترسی
sudo chown -R hiroestate:hiroestate /var/www/hiroestate
```

### پیکربندی پروژه جنگو

```bash
# ایجاد محیط مجازی پایتون
cd /var/www/hiroestate
sudo -u hiroestate python3 -m venv venv

# فعال کردن محیط مجازی
sudo -u hiroestate -H bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u hiroestate -H bash -c "source venv/bin/activate && pip install -r requirements.txt gunicorn"

# اگر فایل requirements.txt ندارید، پکیج‌های پایه را نصب کنید:
sudo -u hiroestate -H bash -c "source venv/bin/activate && pip install django django-filter jdatetime django-jalali psycopg2-binary Pillow python-magic xlsxwriter openpyxl pandas gunicorn"

# ایجاد فایل تنظیمات محلی
sudo nano /var/www/hiroestate/hiro_estate/settings_production.py
```

محتوای فایل `settings_production.py` را به صورت زیر ویرایش کنید:

```python
from .settings import *

# تنظیمات امنیتی
DEBUG = False
SECRET_KEY = 'یک_کلید_محرمانه_قوی_و_تصادفی_اینجا_بنویسید'
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'IP_سرور_شما']

# تنظیمات دیتابیس
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hiroestate',
        'USER': 'hiroestate_user',
        'PASSWORD': 'رمز_عبور_قوی',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# تنظیمات فایل های استاتیک و مدیا
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# تنظیمات امنیتی بیشتر
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 86400  # 1 روز
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

سپس این دستورات را اجرا کنید:

```bash
# مشخص کردن فایل تنظیمات به عنوان فایل پیش‌فرض
sudo -H -u hiroestate bash -c "echo 'export DJANGO_SETTINGS_MODULE=hiro_estate.settings_production' >> /var/www/hiroestate/venv/bin/activate"

# فعال‌سازی محیط مجازی و اجرای مهاجرت‌ها
cd /var/www/hiroestate
sudo -u hiroestate -H bash -c "source venv/bin/activate && python manage.py migrate"

# جمع‌آوری فایل‌های استاتیک
sudo -u hiroestate -H bash -c "source venv/bin/activate && python manage.py collectstatic --noinput"
```

### نصب و پیکربندی Gunicorn

ایجاد فایل پیکربندی Gunicorn:

```bash
sudo -u hiroestate mkdir -p /var/www/hiroestate/run/
sudo nano /var/www/hiroestate/gunicorn_start.sh
```

محتوای فایل `gunicorn_start.sh`:

```bash
#!/bin/bash

NAME="hiroestate"
DIR=/var/www/hiroestate
USER=hiroestate
GROUP=hiroestate
WORKERS=3
BIND=unix:/var/www/hiroestate/run/gunicorn.sock
DJANGO_SETTINGS_MODULE=hiro_estate.settings_production
DJANGO_WSGI_MODULE=hiro_estate.wsgi
LOG_LEVEL=error

cd $DIR
source venv/bin/activate

exec venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $WORKERS \
  --user=$USER \
  --group=$GROUP \
  --bind=$BIND \
  --log-level=$LOG_LEVEL \
  --log-file=-
```

سپس مجوزهای اجرایی را به فایل اضافه کنید:

```bash
sudo chmod +x /var/www/hiroestate/gunicorn_start.sh
```

### راه‌اندازی سرویس سیستمی

برای اطمینان از اجرای خودکار سرویس هنگام راه‌اندازی سرور، یک فایل سرویس سیستمی ایجاد می‌کنیم:

```bash
sudo nano /etc/supervisor/conf.d/hiroestate.conf
```

محتوای فایل پیکربندی supervisor:

```
[program:hiroestate]
command=/var/www/hiroestate/gunicorn_start.sh
user=hiroestate
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/www/hiroestate/logs/gunicorn-error.log
```

ایجاد دایرکتوری لاگ و راه‌اندازی سرویس:

```bash
sudo -u hiroestate mkdir -p /var/www/hiroestate/logs/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status hiroestate
```

### پیکربندی Nginx

```bash
sudo nano /etc/nginx/sites-available/hiroestate
```

محتوای فایل کانفیگ Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 20M;  # افزایش سایز مجاز آپلود

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias /var/www/hiroestate/static/;
    }
    
    location /media/ {
        alias /var/www/hiroestate/media/;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/hiroestate/run/gunicorn.sock;
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }
}
```

فعال‌سازی کانفیگ Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/hiroestate /etc/nginx/sites-enabled
sudo nginx -t  # تست کانفیگ Nginx
sudo systemctl restart nginx
```

### پیکربندی SSL/TLS با Let's Encrypt

برای امن کردن سایت با SSL/TLS رایگان از Let's Encrypt استفاده می‌کنیم:

```bash
# نصب Certbot
sudo apt install -y certbot python3-certbot-nginx

# دریافت و نصب خودکار گواهی SSL
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# تنظیم به‌روزرسانی خودکار گواهی
echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
```

### ایجاد کاربر سوپر ادمین

برای ایجاد کاربر سوپر ادمین این دستورات را اجرا کنید:

```bash
cd /var/www/hiroestate
sudo -u hiroestate -H bash -c "source venv/bin/activate && python manage.py createsuperuser"
```

در این مرحله اطلاعات زیر را وارد کنید:
- نام کاربری
- آدرس ایمیل
- رمز عبور (دوبار)

### تنظیمات فایروال

```bash
# نصب و فعال‌سازی UFW
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing

# اجازه دسترسی به پورت‌های ضروری
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'  # اجازه دسترسی به پورت‌های 80 و 443

# فعال‌سازی فایروال
sudo ufw enable

# بررسی وضعیت
sudo ufw status
```

### پیکربندی پشتیبان‌گیری خودکار

ایجاد اسکریپت پشتیبان‌گیری:

```bash
sudo nano /var/www/hiroestate/backup.sh
```

محتوای فایل اسکریپت:

```bash
#!/bin/bash

# تنظیمات
BACKUP_DIR="/var/backups/hiroestate"
DATETIME=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/hiroestate_db_${DATETIME}.sql"
LOG_FILE="${BACKUP_DIR}/backup_log.txt"

# اطمینان از وجود دایرکتوری
mkdir -p $BACKUP_DIR

# پشتیبان‌گیری از دیتابیس
echo "Starting database backup at $(date)" >> $LOG_FILE
sudo -u postgres pg_dump hiroestate > $BACKUP_FILE
echo "Database backup completed at $(date)" >> $LOG_FILE

# فشرده‌سازی
gzip $BACKUP_FILE
echo "Compressed backup file: ${BACKUP_FILE}.gz" >> $LOG_FILE

# پاک کردن فایل‌های پشتیبان قدیمی (نگهداری فقط 10 فایل آخر)
ls -t ${BACKUP_DIR}/hiroestate_db_*.sql.gz | tail -n +11 | xargs -r rm
echo "Cleaned old backup files at $(date)" >> $LOG_FILE

# پشتیبان‌گیری از فایل‌های مدیا
MEDIA_BACKUP="${BACKUP_DIR}/hiroestate_media_${DATETIME}.tar.gz"
tar -czf $MEDIA_BACKUP /var/www/hiroestate/media
echo "Media backup completed at $(date): $MEDIA_BACKUP" >> $LOG_FILE

# پاک کردن فایل‌های مدیا قدیمی (نگهداری فقط 3 فایل آخر)
ls -t ${BACKUP_DIR}/hiroestate_media_*.tar.gz | tail -n +4 | xargs -r rm
echo "Cleaned old media backup files at $(date)" >> $LOG_FILE
```

تنظیم مجوزها و زمان‌بندی خودکار:

```bash
# اعطای مجوز اجرا به اسکریپت
sudo chmod +x /var/www/hiroestate/backup.sh

# ایجاد زمان‌بندی Cron برای اجرای روزانه
echo "0 2 * * * root /var/www/hiroestate/backup.sh" | sudo tee -a /etc/crontab > /dev/null
```

## بررسی نهایی و راه‌اندازی

پس از انجام همه مراحل بالا، سیستم هوشمند مدیریت املاک هیرو روی سرور شما نصب شده و از طریق آدرس دامنه با پروتکل HTTPS در دسترس خواهد بود. برای اطمینان از راه‌اندازی موفق، سرویس‌های زیر را بررسی کنید:

```bash
# بررسی وضعیت Nginx
sudo systemctl status nginx

# بررسی وضعیت Supervisor
sudo supervisorctl status hiroestate

# بررسی لاگ‌های Gunicorn
sudo tail -f /var/www/hiroestate/logs/gunicorn-error.log
```

سیستم باید از طریق مرورگر در آدرس `https://your-domain.com` در دسترس باشد. با استفاده از نام کاربری و رمز عبور سوپر ادمین که ایجاد کردید، می‌توانید به پنل مدیریت در آدرس `https://your-domain.com/admin/` وارد شوید.

## عیب‌یابی مشکلات رایج

1. **خطای دسترسی به فایل‌ها**: بررسی مجوزهای دسترسی با `sudo chown -R hiroestate:hiroestate /var/www/hiroestate`
2. **خطای اتصال به دیتابیس**: بررسی تنظیمات دیتابیس و رمز عبور در فایل `settings_production.py`
3. **مشکل Nginx**: بررسی لاگ‌ها با `sudo tail -f /var/log/nginx/error.log`
4. **عدم اجرای Gunicorn**: بررسی لاگ‌ها با `sudo tail -f /var/www/hiroestate/logs/gunicorn-error.log`

## نگهداری سیستم

**به‌روزرسانی سیستم**:
```bash
cd /var/www/hiroestate
sudo -u hiroestate -H bash -c "source venv/bin/activate && git pull"  # در صورت استفاده از Git
sudo -u hiroestate -H bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u hiroestate -H bash -c "source venv/bin/activate && python manage.py migrate"
sudo -u hiroestate -H bash -c "source venv/bin/activate && python manage.py collectstatic --noinput"
sudo supervisorctl restart hiroestate
```

**به‌روزرسانی امنیتی سرور**:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

سیستم مدیریت املاک هیرو یک نرم‌افزار تحت وب و کاملاً فارسی است که برای مدیریت املاک و مستغلات طراحی شده است. این سیستم با استفاده از فریم‌ورک جنگو (Django) پیاده‌سازی شده و دارای رابط کاربری RTL فارسی، امکانات مدیریت املاک، جستجوی پیشرفته، داشبورد و سیستم پشتیبان‌گیری است.

## ویژگی‌های سیستم

- **احراز هویت و مدیریت دسترسی‌ها**:
  - سطوح دسترسی متفاوت برای کاربران (مدیر ارشد، مدیر املاک، کارشناس فروش)
  - فرم ورود فارسی و RTL
  - سیستم قفل حساب پس از چند تلاش ناموفق (محافظت در برابر حملات Brute Force)
  - کنترل دقیق دسترسی‌ها بر اساس نقش کاربر

- **مدیریت املاک**:
  - ثبت و مدیریت املاک با اطلاعات کامل
  - تولید کد یکتا برای هر ملک به صورت خودکار
  - تعیین وضعیت ملک (موجود، فروخته شده، اجاره داده شده و...)
  - مدیریت تصاویر املاک
  - نمایش اطلاعات ملک به صورت کارت‌های گرافیکی جذاب

- **جستجو و فیلتر پیشرفته**:
  - جستجو بر اساس کد ملک، آدرس، قیمت، متراژ و...
  - فیلتر بر اساس نوع معامله، نوع ملک و وضعیت
  - نمایش نتایج جستجو به صورت بلادرنگ

- **سیستم پشتیبان‌گیری و بازیابی**:
  - امکان تهیه فایل پشتیبان از کل اطلاعات
  - بازیابی اطلاعات از فایل پشتیبان
  - تاریخچه کامل پشتیبان‌گیری‌ها
  - رابط کاربری گرافیکی برای مدیریت پشتیبان‌ها

- **تنظیمات سیستم**:
  - بیش از 40 تنظیم مختلف برای شخصی‌سازی سیستم
  - تغییر عنوان سایت
  - آپلود لوگو و آیکون‌های سفارشی
  - تغییر فونت (وزیر یا ایران‌سنس)
  - تعیین تصویر پیش‌فرض برای املاک
  - تنظیمات شبکه‌های اجتماعی، درگاه پرداخت و تحلیل آماری

- **داشبورد مدیریتی**:
  - نمایش آمار و ارقام کلیدی
  - نمودارهای پویا و تعاملی
  - کارت‌های آماری با انیمیشن
  - گزارش‌های وضعیت فروش، اجاره و درآمد

- **امنیت پیشرفته**:
  - محافظت در برابر حملات XSS, CSRF, SQL Injection
  - محدودیت نرخ درخواست برای مقابله با حملات DDoS
  - قفل حساب کاربری پس از چند تلاش ناموفق
  - امنیت نشست‌ها و محافظت در برابر Session Hijacking
  - سیاست امنیت محتوا (CSP)
  - ثبت وقایع امنیتی و هشدار تخلفات
  - داشبورد امنیتی برای مدیران سیستم

- **رابط کاربری واکنش‌گرا**:
  - طراحی متناسب با دستگاه‌های مختلف (موبایل، تبلت، دسکتاپ)
  - انیمیشن‌های جذاب و روان
  - رابط RTL کاملاً فارسی
  - تجربه کاربری بهینه شده

## نیازمندی‌ها

- Python 3.8+ 
- Django 5.2+
- PostgreSQL (برای محیط تولید)
- SQLite (برای محیط توسعه)
- پکیج‌های زیر:
  - django-filter
  - django-jalali
  - jdatetime
  - Pillow
  - openpyxl
  - psycopg2-binary
  - python-magic
  - xlsxwriter
  - dj-database-url

## نصب و راه‌اندازی

### روش اول: نصب روی سرور محلی

1. **کلون پروژه**:
   ```bash
   git clone https://github.com/yourusername/hiro-estate.git
   cd hiro-estate
   ```

2. **نصب وابستگی‌ها**:
   ```bash
   pip install -r requirements.txt
   ```

3. **اجرای مهاجرت‌های پایگاه داده**:
   ```bash
   python manage.py migrate
   ```

4. **ایجاد کاربر مدیر**:
   ```bash
   python manage.py create_superuser
   ```

5. **اضافه کردن داده‌های اولیه**:
   ```bash
   python manage.py create_initial_data
   ```

6. **اجرای سرور توسعه**:
   ```bash
   python manage.py runserver
   ```

### روش دوم: استفاده از Docker

1. **ساخت و اجرای کانتینر**:
   ```bash
   docker-compose up -d
   ```

2. **ایجاد کاربر مدیر در داخل کانتینر**:
   ```bash
   docker-compose exec web python manage.py create_superuser
   ```

## ساختار پروژه

```
hiro_estate/
├── accounts/          # ماژول مدیریت کاربران و احراز هویت
├── config/            # ماژول تنظیمات و پیکربندی سیستم
├── dashboard/         # ماژول داشبورد مدیریتی
├── hiro_estate/       # تنظیمات اصلی Django
├── logs/              # فایل‌های لاگ سیستم و امنیتی
├── media/             # فایل‌های آپلود شده
├── properties/        # ماژول مدیریت املاک
├── static/            # فایل‌های استاتیک (CSS, JavaScript)
└── templates/         # قالب‌های HTML
```

## ویژگی‌های امنیتی

- **میدل‌ویرهای امنیتی سفارشی**:
  - RateLimitMiddleware: محدودیت نرخ درخواست
  - EnhancedSecurityMiddleware: محافظت در برابر انواع تزریق
  - AccountLockoutMiddleware: قفل حساب پس از تلاش‌های ناموفق
  - ContentSecurityPolicyMiddleware: سیاست امنیت محتوا
  - SessionSecurityMiddleware: امنیت نشست‌ها

- **امنیت پایگاه داده**:
  - محافظت در برابر SQL Injection
  - Connection pooling و مدیریت اتصالات
  - پشتیبان‌گیری خودکار و دوره‌ای

- **امنیت لایه وب**:
  - هدرهای امنیتی HTTP
  - دیوار آتش لایه وب برای تشخیص و مسدود کردن حملات
  - ردیابی و ثبت وقایع امنیتی

## راهنمای استفاده

### ورود به سیستم

برای ورود به سیستم، به آدرس `/accounts/login/` مراجعه کنید. لطفاً از اطلاعات حساب کاربری که مدیر سیستم برای شما تعریف کرده استفاده نمایید. پس از اولین ورود، توصیه می‌شود رمز عبور خود را تغییر دهید.

### مدیریت املاک

برای مدیریت املاک به بخش "املاک" در منوی اصلی بروید. در این بخش می‌توانید:
- املاک جدید اضافه کنید
- املاک موجود را ویرایش کنید
- تصاویر املاک را مدیریت کنید
- وضعیت املاک را تغییر دهید

### تنظیمات سیستم

برای تغییر تنظیمات سیستم، به بخش "تنظیمات" در منوی ادمین بروید. این بخش شامل:
- تنظیمات عمومی
- تنظیمات ظاهری
- تنظیمات امنیتی
- تنظیمات پشتیبان‌گیری

## مشارکت در توسعه

از مشارکت شما در توسعه این پروژه استقبال می‌کنیم. لطفاً برای مشارکت:

1. پروژه را fork کنید
2. یک branch جدید ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات خود را commit کنید (`git commit -m 'Add some amazing feature'`)
4. به ریپوزیتوری خود push کنید (`git push origin feature/amazing-feature`)
5. یک Pull Request ایجاد کنید

## مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر، فایل `LICENSE` را مطالعه کنید.

## تماس با ما

برای هرگونه سوال یا پیشنهاد، لطفاً با ما از طریق ایمیل [example@domain.com](mailto:example@domain.com) در تماس باشید.