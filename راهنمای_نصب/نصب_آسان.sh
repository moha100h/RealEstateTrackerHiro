#!/bin/bash
# اسکریپت نصب آسان سیستم هیرو املاک
# این اسکریپت به صورت خودکار تمامی مراحل نصب را انجام می‌دهد

echo "================================================"
echo "  نصب آسان سیستم مدیریت هیرو املاک  "
echo "================================================"

# بررسی اجرای با دسترسی روت
if [ "$(id -u)" != "0" ]; then
   echo "این اسکریپت باید با دسترسی روت اجرا شود. لطفاً با دستور sudo اجرا کنید." 
   exit 1
fi

# پرسیدن اطلاعات از کاربر
read -p "نام دامنه سایت (بدون http/https، مثلاً yourdomain.com): " DOMAIN_NAME
read -p "آدرس IP سرور: " SERVER_IP
read -p "نام کاربری دیتابیس (پیش‌فرض: hiroestate): " DB_USER
DB_USER=${DB_USER:-hiroestate}
read -s -p "رمز عبور دیتابیس: " DB_PASSWORD
echo ""
read -p "نام دیتابیس (پیش‌فرض: hiroestate): " DB_NAME
DB_NAME=${DB_NAME:-hiroestate}

# تولید کلید محرمانه تصادفی
SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*(-_=+)' | fold -w 50 | head -n 1)

echo "به‌روزرسانی بسته‌های سیستم..."
apt update && apt upgrade -y

echo "نصب پیش‌نیازها..."
apt install -y python3-pip python3-dev python3-venv postgresql postgresql-contrib nginx curl git

echo "تنظیم کاربر سیستمی..."
useradd -m -s /bin/bash hiroestate || true  # ایجاد کاربر اگر وجود نداشته باشد
usermod -aG sudo hiroestate || true  # اضافه کردن به گروه sudo

echo "ایجاد دیتابیس PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || true
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'Asia/Tehran';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "ایجاد پوشه نصب..."
mkdir -p /var/www/hiroestate
chown -R hiroestate:hiroestate /var/www/hiroestate

# اگر کد پروژه در همان پوشه است، آن را به محل نصب کپی کنید
if [ -f "$(dirname "$0")/../manage.py" ]; then
    echo "کپی کردن فایل‌های پروژه به محل نصب..."
    cp -r "$(dirname "$0")/../"* /var/www/hiroestate/
else
    echo "خطا: فایل‌های پروژه پیدا نشد."
    exit 1
fi

# ایجاد محیط مجازی و نصب وابستگی‌ها
echo "ایجاد محیط مجازی و نصب وابستگی‌ها..."
cd /var/www/hiroestate
python3 -m venv venv
su -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt gunicorn" hiroestate

# ایجاد فایل تنظیمات تولید
echo "ایجاد فایل تنظیمات تولید..."
cat > /var/www/hiroestate/hiro_estate/settings_production.py << EOF
"""
تنظیمات محیط تولید هیرو املاک - تنظیم شده توسط اسکریپت نصب
"""

import os
from .settings import *

# تنظیمات امنیتی
DEBUG = False
SECRET_KEY = '$SECRET_KEY'

# تنظیمات میزبان‌های مجاز
ALLOWED_HOSTS = ['$DOMAIN_NAME', 'www.$DOMAIN_NAME', '$SERVER_IP']

# تنظیمات پایگاه داده
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '$DB_NAME',
        'USER': '$DB_USER',
        'PASSWORD': '$DB_PASSWORD',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# تنظیمات فایل‌های استاتیک
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# حل مشکل STATICFILES_DIRS
STATICFILES_DIRS = []  # خالی کردن لیست STATICFILES_DIRS در محیط تولید

# تنظیمات فایل‌های رسانه‌ای
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ایجاد پوشه‌های مورد نیاز
for folder in ['logs', 'media', 'static', 'cache']:
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
EOF

# تنظیم متغیر محیطی برای استفاده از تنظیمات تولید
echo "تنظیم متغیر محیطی DJANGO_SETTINGS_MODULE..."
echo 'export DJANGO_SETTINGS_MODULE="hiro_estate.settings_production"' >> /var/www/hiroestate/venv/bin/activate

# اجرای مایگریشن‌ها و جمع‌آوری فایل‌های استاتیک
echo "اجرای مایگریشن‌ها و جمع‌آوری فایل‌های استاتیک..."
su -c "source /var/www/hiroestate/venv/bin/activate && python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --noinput" hiroestate

# ایجاد فایل سرویس گانیکورن
echo "ایجاد فایل سرویس گانیکورن..."
cat > /etc/systemd/system/gunicorn_hiroestate.service << EOF
[Unit]
Description=gunicorn daemon for Hiro Estate
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/hiroestate
Environment="DJANGO_SETTINGS_MODULE=hiro_estate.settings_production"
ExecStart=/var/www/hiroestate/venv/bin/gunicorn --workers 3 --bind unix:/var/www/hiroestate/hiroestate.sock hiro_estate.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# ایجاد فایل کانفیگ انجین‌اکس
echo "ایجاد فایل کانفیگ انجین‌اکس..."
cat > /etc/nginx/sites-available/hiroestate << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/hiroestate;
    }
    
    location /media/ {
        root /var/www/hiroestate;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/hiroestate/hiroestate.sock;
    }
}
EOF

# فعال‌سازی کانفیگ انجین‌اکس
echo "فعال‌سازی کانفیگ انجین‌اکس..."
ln -sf /etc/nginx/sites-available/hiroestate /etc/nginx/sites-enabled
rm -f /etc/nginx/sites-enabled/default  # حذف کانفیگ پیش‌فرض

# تنظیم مجوزهای دسترسی
echo "تنظیم مجوزهای دسترسی..."
mkdir -p /var/www/hiroestate/media /var/www/hiroestate/static
chown -R www-data:www-data /var/www/hiroestate
find /var/www/hiroestate -type d -exec chmod 755 {} \;
find /var/www/hiroestate -type f -exec chmod 644 {} \;
chmod -R 775 /var/www/hiroestate/media /var/www/hiroestate/static

# راه‌اندازی سرویس‌ها
echo "راه‌اندازی سرویس‌ها..."
systemctl enable gunicorn_hiroestate
systemctl start gunicorn_hiroestate
nginx -t && systemctl restart nginx

echo ""
echo "==================== نصب با موفقیت انجام شد! ===================="
echo ""
echo "سیستم هیرو املاک روی $DOMAIN_NAME نصب شد."
echo ""
echo "اطلاعات مهم:"
echo "- آدرس پنل مدیریت: http://$DOMAIN_NAME/admin/"
echo "- برای ایجاد کاربر ابرمدیر، از دستور زیر استفاده کنید:"
echo "  sudo -u hiroestate -H bash -c \"source /var/www/hiroestate/venv/bin/activate && python /var/www/hiroestate/manage.py createsuperuser\""
echo ""
echo "توصیه می‌شود برای امنیت بیشتر، SSL را با Let's Encrypt تنظیم کنید:"
echo "sudo apt install -y certbot python3-certbot-nginx"
echo "sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME"
echo ""
echo "================================================================"