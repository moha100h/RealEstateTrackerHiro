#!/bin/bash
# اسکریپت نصب خودکار سیستم هوشمند مدیریت املاک هیرو
# نویسنده: تیم توسعه هیرو املاک
# تاریخ: ۱۴۰۴/۰۲/۲۱

# رنگ‌ها برای خروجی زیباتر
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # بدون رنگ

# تنظیمات پیش‌فرض
INSTALL_DIR="/var/www/hiroestate"
DB_NAME="hiroestate"
DB_USER="hiroestate_user"
DB_PASSWORD=""
DB_HOST="localhost"
DB_PORT="5432"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD=""
ADMIN_EMAIL=""
DOMAIN_NAME=""
USE_DOCKER=false

# فانکشن نمایش خطا و خروج
function error_exit {
    echo -e "${RED}خطا: $1${NC}" >&2
    exit 1
}

# فانکشن نمایش اطلاعات
function info {
    echo -e "${BLUE}اطلاعات: $1${NC}"
}

# فانکشن نمایش موفقیت
function success {
    echo -e "${GREEN}موفقیت: $1${NC}"
}

# فانکشن نمایش هشدار
function warning {
    echo -e "${YELLOW}هشدار: $1${NC}"
}

# بررسی اجرا با دسترسی روت
if [[ $EUID -ne 0 ]]; then
   error_exit "این اسکریپت باید با دسترسی روت اجرا شود. لطفاً با sudo امتحان کنید."
fi

# نمایش خوش‌آمدگویی
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  نصب‌کننده خودکار سیستم مدیریت املاک هیرو  ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""

# دریافت اطلاعات از کاربر
read -p "مسیر نصب [$INSTALL_DIR]: " input
INSTALL_DIR=${input:-$INSTALL_DIR}

echo ""
echo "--- اطلاعات دیتابیس ---"
read -p "نام دیتابیس [$DB_NAME]: " input
DB_NAME=${input:-$DB_NAME}

read -p "کاربر دیتابیس [$DB_USER]: " input
DB_USER=${input:-$DB_USER}

read -sp "رمز عبور دیتابیس: " DB_PASSWORD
echo ""

read -p "میزبان دیتابیس [$DB_HOST]: " input
DB_HOST=${input:-$DB_HOST}

read -p "پورت دیتابیس [$DB_PORT]: " input
DB_PORT=${input:-$DB_PORT}

echo ""
echo "--- اطلاعات مدیر سیستم ---"
read -p "نام کاربری مدیر [$ADMIN_USERNAME]: " input
ADMIN_USERNAME=${input:-$ADMIN_USERNAME}

read -sp "رمز عبور مدیر: " ADMIN_PASSWORD
echo ""

read -p "ایمیل مدیر: " ADMIN_EMAIL

echo ""
echo "--- اطلاعات سرور ---"
read -p "نام دامنه (مثال: example.com): " DOMAIN_NAME

echo ""
read -p "آیا می‌خواهید از Docker استفاده کنید؟ (y/n) [n]: " input
if [[ $input == "y" || $input == "Y" ]]; then
    USE_DOCKER=true
fi

# تولید کلید امنیتی تصادفی
SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*()_+' | fold -w 50 | head -n 1)

# ایجاد دایرکتوری نصب
echo ""
info "ایجاد دایرکتوری نصب..."
mkdir -p $INSTALL_DIR || error_exit "خطا در ایجاد دایرکتوری $INSTALL_DIR"

# کپی فایل‌های پروژه
info "کپی فایل‌های پروژه..."
cp -r ./* $INSTALL_DIR/ || error_exit "خطا در کپی فایل‌ها به $INSTALL_DIR"

# اگر از Docker استفاده نمی‌کنیم، نصب مستقیم
if [ "$USE_DOCKER" = false ]; then
    # نصب پیش‌نیازها
    info "نصب پیش‌نیازها..."
    apt-get update || error_exit "خطا در به‌روزرسانی مخازن"
    apt-get install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx || error_exit "خطا در نصب پیش‌نیازها"
    
    # ایجاد دیتابیس PostgreSQL
    info "ایجاد دیتابیس PostgreSQL..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || warning "دیتابیس ممکن است از قبل موجود باشد"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || warning "کاربر دیتابیس ممکن است از قبل موجود باشد"
    sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
    sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
    sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    # ایجاد محیط مجازی و نصب وابستگی‌ها
    info "ایجاد محیط مجازی و نصب وابستگی‌ها..."
    cd $INSTALL_DIR
    python3 -m venv venv || error_exit "خطا در ایجاد محیط مجازی"
    source venv/bin/activate
    pip install Django==5.2 dj-database-url==2.3.0 psycopg2-binary==2.9.9 Pillow==11.2.1 python-magic==0.4.27 django-filter==25.1 jdatetime==4.1.1 django-jalali==6.0.1 xlsxwriter==3.2.0 openpyxl==3.1.6 pandas==2.2.1 gunicorn==22.0.0 python-dotenv==1.0.1 whitenoise==6.6.0 || error_exit "خطا در نصب پکیج‌ها"
    
    # ایجاد فایل .env
    info "ایجاد فایل .env..."
    cat > $INSTALL_DIR/.env << EOL
DEBUG=False
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME,localhost,127.0.0.1
EOL
    
    # اجرای مهاجرت‌ها
    info "اجرای مهاجرت‌ها..."
    python manage.py migrate || error_exit "خطا در اجرای مهاجرت‌ها"
    python manage.py collectstatic --noinput || error_exit "خطا در جمع‌آوری فایل‌های استاتیک"
    
    # ایجاد کاربر مدیر
    info "ایجاد کاربر مدیر..."
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')" | python manage.py shell || warning "خطا در ایجاد کاربر مدیر (ممکن است از قبل موجود باشد)"
    
    # تنظیم Gunicorn
    info "تنظیم Gunicorn..."
    cat > /etc/systemd/system/hiroestate.service << EOL
[Unit]
Description=Hiro Estate Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --workers 3 --bind unix:$INSTALL_DIR/hiroestate.sock hiro_estate.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL
    
    # تنظیم مجوزها
    info "تنظیم مجوزها..."
    chown -R www-data:www-data $INSTALL_DIR
    chmod -R 755 $INSTALL_DIR
    
    # راه‌اندازی Gunicorn
    info "راه‌اندازی Gunicorn..."
    systemctl daemon-reload
    systemctl start hiroestate
    systemctl enable hiroestate
    
    # تنظیم Nginx
    info "تنظیم Nginx..."
    cat > /etc/nginx/sites-available/hiroestate << EOL
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root $INSTALL_DIR;
    }
    
    location /media/ {
        root $INSTALL_DIR;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:$INSTALL_DIR/hiroestate.sock;
    }
}
EOL
    
    # فعال‌سازی سایت Nginx
    ln -s /etc/nginx/sites-available/hiroestate /etc/nginx/sites-enabled || warning "سایت Nginx ممکن است از قبل فعال باشد"
    nginx -t || error_exit "خطا در کانفیگ Nginx"
    systemctl restart nginx
    
else
    # استفاده از Docker
    info "تنظیم Docker..."
    
    # بررسی نصب Docker
    if ! command -v docker &> /dev/null; then
        info "نصب Docker..."
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        apt-get update
        apt-get install -y docker-ce docker-compose
    fi
    
    # ایجاد فایل .env برای Docker
    info "ایجاد فایل .env برای Docker..."
    cat > $INSTALL_DIR/.env << EOL
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgres://$DB_USER:$DB_PASSWORD@db:5432/$DB_NAME
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME,localhost,127.0.0.1
EOL
    
    # تنظیم فایل docker-compose.yml
    info "تنظیم فایل docker-compose.yml..."
    # این فایل قبلاً کپی شده است
    
    # اجرای Docker Compose
    info "اجرای Docker Compose..."
    cd $INSTALL_DIR
    docker-compose up -d || error_exit "خطا در اجرای Docker Compose"
    
    # ایجاد کاربر مدیر
    info "ایجاد کاربر مدیر..."
    sleep 10 # صبر برای آماده‌سازی کامل کانتینرها
    docker-compose exec web python manage.py createsuperuser --noinput --username $ADMIN_USERNAME --email $ADMIN_EMAIL || warning "خطا در ایجاد کاربر مدیر (ممکن است از قبل موجود باشد)"
    docker-compose exec web python -c "from django.contrib.auth.models import User; u = User.objects.get(username='$ADMIN_USERNAME'); u.set_password('$ADMIN_PASSWORD'); u.save()"
fi

# نمایش اطلاعات تکمیلی
success "نصب سیستم هوشمند مدیریت املاک هیرو با موفقیت انجام شد!"
echo ""
echo -e "${GREEN}==================================================${NC}"
echo -e "  آدرس سایت: http://$DOMAIN_NAME"
echo -e "  آدرس مدیریت: http://$DOMAIN_NAME/admin/"
echo -e "  نام کاربری مدیر: $ADMIN_USERNAME"
echo -e "  رمز عبور مدیر: (رمز انتخابی شما)"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo -e "برای اطلاعات بیشتر لطفاً به فایل راهنمای نصب مراجعه کنید."
echo -e "از انتخاب سیستم هوشمند مدیریت املاک هیرو متشکریم!"