#!/bin/bash
# اسکریپت بازیابی اطلاعات سیستم هوشمند مدیریت املاک هیرو
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
BACKUP_DIR="/var/backups/hiroestate"
DB_NAME="hiroestate"
DB_USER="hiroestate_user"
DB_PASSWORD=""
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DATE=""
USE_DOCKER=false
RESTORE_DB=true
RESTORE_MEDIA=true
RESTORE_SETTINGS=false
FORCE_RESTORE=false

# فانکشن نمایش راهنما
function show_help {
    echo "اسکریپت بازیابی سیستم هوشمند مدیریت املاک هیرو"
    echo ""
    echo "استفاده:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "گزینه‌ها:"
    echo "  --help                  نمایش این راهنما"
    echo "  --backup-dir=DIR        مسیر پوشه پشتیبان (پیش‌فرض: $BACKUP_DIR)"
    echo "  --install-dir=DIR       مسیر نصب سیستم (پیش‌فرض: $INSTALL_DIR)"
    echo "  --date=DATE             تاریخ پشتیبان برای بازیابی (فرمت: YYYY-MM-DD_HH-MM-SS)"
    echo "  --docker                استفاده از Docker برای بازیابی"
    echo "  --db-name=NAME          نام دیتابیس (پیش‌فرض: $DB_NAME)"
    echo "  --db-user=USER          نام کاربری دیتابیس (پیش‌فرض: $DB_USER)"
    echo "  --db-password=PASS      رمز عبور دیتابیس"
    echo "  --db-host=HOST          میزبان دیتابیس (پیش‌فرض: $DB_HOST)"
    echo "  --db-port=PORT          پورت دیتابیس (پیش‌فرض: $DB_PORT)"
    echo "  --no-db                 عدم بازیابی دیتابیس"
    echo "  --no-media              عدم بازیابی فایل‌های رسانه"
    echo "  --restore-settings      بازیابی تنظیمات"
    echo "  --force                 بازیابی بدون درخواست تأیید"
    echo ""
    echo "مثال:"
    echo "  $0 --date=2024-05-01_12-00-00 --force"
    echo "  $0 --backup-dir=/path/to/backups --date=2024-05-01_12-00-00 --docker"
    exit 0
}

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

# پردازش پارامترهای ورودی
for i in "$@"; do
    case $i in
        --help)
            show_help
            ;;
        --backup-dir=*)
            BACKUP_DIR="${i#*=}"
            shift
            ;;
        --install-dir=*)
            INSTALL_DIR="${i#*=}"
            shift
            ;;
        --date=*)
            BACKUP_DATE="${i#*=}"
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --db-name=*)
            DB_NAME="${i#*=}"
            shift
            ;;
        --db-user=*)
            DB_USER="${i#*=}"
            shift
            ;;
        --db-password=*)
            DB_PASSWORD="${i#*=}"
            shift
            ;;
        --db-host=*)
            DB_HOST="${i#*=}"
            shift
            ;;
        --db-port=*)
            DB_PORT="${i#*=}"
            shift
            ;;
        --no-db)
            RESTORE_DB=false
            shift
            ;;
        --no-media)
            RESTORE_MEDIA=false
            shift
            ;;
        --restore-settings)
            RESTORE_SETTINGS=true
            shift
            ;;
        --force)
            FORCE_RESTORE=true
            shift
            ;;
        *)
            warning "پارامتر ناشناخته: $i"
            ;;
    esac
done

# بررسی پارامترهای اجباری
if [ -z "$BACKUP_DATE" ]; then
    # اگر تاریخ مشخص نشده، آخرین پشتیبان را استفاده می‌کنیم
    LATEST_DB=$(ls -t "$BACKUP_DIR"/hiroestate_db_*.* 2>/dev/null | head -n 1)
    if [ -z "$LATEST_DB" ]; then
        error_exit "هیچ پشتیبانی یافت نشد. لطفاً تاریخ پشتیبان را با --date مشخص کنید."
    else
        BACKUP_DATE=$(basename "$LATEST_DB" | sed 's/hiroestate_db_\(.*\)\..*/\1/')
        warning "تاریخ پشتیبان مشخص نشده، از آخرین پشتیبان استفاده می‌شود: $BACKUP_DATE"
    fi
fi

# بررسی وجود فایل‌های پشتیبان
DB_BACKUP_FILE=""
if [ -f "$BACKUP_DIR/hiroestate_db_$BACKUP_DATE.backup" ]; then
    DB_BACKUP_FILE="$BACKUP_DIR/hiroestate_db_$BACKUP_DATE.backup"
elif [ -f "$BACKUP_DIR/hiroestate_db_$BACKUP_DATE.sql" ]; then
    DB_BACKUP_FILE="$BACKUP_DIR/hiroestate_db_$BACKUP_DATE.sql"
else
    error_exit "فایل پشتیبان دیتابیس برای تاریخ $BACKUP_DATE یافت نشد."
fi

MEDIA_BACKUP_FILE="$BACKUP_DIR/hiroestate_media_$BACKUP_DATE.tar.gz"
if [ ! -f "$MEDIA_BACKUP_FILE" ] && [ "$RESTORE_MEDIA" = true ]; then
    warning "فایل پشتیبان رسانه برای تاریخ $BACKUP_DATE یافت نشد."
    read -p "آیا می‌خواهید بدون بازیابی فایل‌های رسانه ادامه دهید؟ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error_exit "بازیابی توسط کاربر لغو شد."
    fi
    RESTORE_MEDIA=false
fi

SETTINGS_BACKUP_FILE="$BACKUP_DIR/hiroestate_settings_$BACKUP_DATE.tar.gz"
if [ ! -f "$SETTINGS_BACKUP_FILE" ] && [ "$RESTORE_SETTINGS" = true ]; then
    warning "فایل پشتیبان تنظیمات برای تاریخ $BACKUP_DATE یافت نشد."
    read -p "آیا می‌خواهید بدون بازیابی تنظیمات ادامه دهید؟ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error_exit "بازیابی توسط کاربر لغو شد."
    fi
    RESTORE_SETTINGS=false
fi

# نمایش اطلاعات بازیابی
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  بازیابی سیستم هوشمند مدیریت املاک هیرو  ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo -e "تاریخ پشتیبان: $BACKUP_DATE"
echo -e "مسیر نصب: $INSTALL_DIR"
echo -e "مسیر پشتیبان: $BACKUP_DIR"
echo -e "استفاده از Docker: $(if [ "$USE_DOCKER" = true ]; then echo "بله"; else echo "خیر"; fi)"
echo ""
echo -e "بازیابی دیتابیس: $(if [ "$RESTORE_DB" = true ]; then echo "بله"; else echo "خیر"; fi)"
if [ "$RESTORE_DB" = true ]; then
    echo -e "  فایل دیتابیس: $(basename "$DB_BACKUP_FILE")"
    echo -e "  نام دیتابیس: $DB_NAME"
    echo -e "  کاربر دیتابیس: $DB_USER"
fi
echo -e "بازیابی فایل‌های رسانه: $(if [ "$RESTORE_MEDIA" = true ]; then echo "بله"; else echo "خیر"; fi)"
if [ "$RESTORE_MEDIA" = true ]; then
    echo -e "  فایل رسانه: $(basename "$MEDIA_BACKUP_FILE")"
fi
echo -e "بازیابی تنظیمات: $(if [ "$RESTORE_SETTINGS" = true ]; then echo "بله"; else echo "خیر"; fi)"
if [ "$RESTORE_SETTINGS" = true ]; then
    echo -e "  فایل تنظیمات: $(basename "$SETTINGS_BACKUP_FILE")"
fi
echo ""

# درخواست تأیید از کاربر
if [ "$FORCE_RESTORE" != true ]; then
    read -p "آیا از بازیابی با تنظیمات فوق اطمینان دارید؟ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error_exit "بازیابی توسط کاربر لغو شد."
    fi
fi

# بررسی دسترسی به دایرکتوری نصب
if [ ! -d "$INSTALL_DIR" ]; then
    error_exit "دایرکتوری نصب $INSTALL_DIR وجود ندارد."
fi

# بررسی اجرا با دسترسی روت
if [[ $EUID -ne 0 ]]; then
   warning "این اسکریپت بدون دسترسی روت اجرا می‌شود. ممکن است با مشکل مواجه شوید."
   read -p "آیا می‌خواهید ادامه دهید؟ (y/n) " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       error_exit "بازیابی توسط کاربر لغو شد."
   fi
fi

# بازیابی دیتابیس
if [ "$RESTORE_DB" = true ]; then
    info "در حال بازیابی دیتابیس..."
    
    if [ "$USE_DOCKER" = true ]; then
        # استفاده از Docker
        cd "$INSTALL_DIR" || error_exit "دایرکتوری نصب یافت نشد"
        
        if [[ "$DB_BACKUP_FILE" == *.sql ]]; then
            # فایل SQL
            cat "$DB_BACKUP_FILE" | docker-compose exec -T db psql -U "$DB_USER" "$DB_NAME" || error_exit "خطا در بازیابی دیتابیس"
        else
            # فایل بازیابی باینری
            docker cp "$DB_BACKUP_FILE" $(docker-compose ps -q db):/tmp/db_backup.backup || error_exit "خطا در کپی فایل پشتیبان به کانتینر"
            docker-compose exec -T db pg_restore -U "$DB_USER" -d "$DB_NAME" -c /tmp/db_backup.backup || error_exit "خطا در بازیابی دیتابیس"
        fi
    else
        # نصب مستقیم
        if [ -z "$DB_PASSWORD" ]; then
            # خواندن رمز از فایل .env
            if [ -f "$INSTALL_DIR/.env" ]; then
                DB_PASSWORD=$(grep -o "DATABASE_URL=postgres://[^:]*:\([^@]*\)@" "$INSTALL_DIR/.env" | sed 's/.*://' | sed 's/@//')
            fi
        fi
        
        if [[ "$DB_BACKUP_FILE" == *.sql ]]; then
            # فایل SQL
            PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$DB_BACKUP_FILE" || error_exit "خطا در بازیابی دیتابیس"
        else
            # فایل بازیابی باینری
            PGPASSWORD="$DB_PASSWORD" pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$DB_BACKUP_FILE" || error_exit "خطا در بازیابی دیتابیس"
        fi
    fi
    
    success "دیتابیس با موفقیت بازیابی شد."
fi

# بازیابی فایل‌های رسانه
if [ "$RESTORE_MEDIA" = true ]; then
    info "در حال بازیابی فایل‌های رسانه..."
    
    if [ "$USE_DOCKER" = true ]; then
        # استفاده از Docker
        cd "$INSTALL_DIR" || error_exit "دایرکتوری نصب یافت نشد"
        docker cp "$MEDIA_BACKUP_FILE" $(docker-compose ps -q web):/tmp/media_backup.tar.gz || error_exit "خطا در کپی فایل پشتیبان به کانتینر"
        docker-compose exec -T web bash -c "mkdir -p /app/media && rm -rf /app/media/* && tar -xzf /tmp/media_backup.tar.gz -C /app" || warning "خطا در بازیابی فایل‌های رسانه"
    else
        # نصب مستقیم
        rm -rf "$INSTALL_DIR/media"
        mkdir -p "$INSTALL_DIR/media"
        tar -xzf "$MEDIA_BACKUP_FILE" -C "$INSTALL_DIR" || warning "خطا در بازیابی فایل‌های رسانه"
    fi
    
    # تنظیم مجوزها
    if [ "$USE_DOCKER" = false ]; then
        chown -R www-data:www-data "$INSTALL_DIR/media" 2>/dev/null || warning "خطا در تنظیم مجوزها"
        chmod -R 755 "$INSTALL_DIR/media" 2>/dev/null || warning "خطا در تنظیم مجوزها"
    fi
    
    success "فایل‌های رسانه با موفقیت بازیابی شدند."
fi

# بازیابی تنظیمات
if [ "$RESTORE_SETTINGS" = true ]; then
    info "در حال بازیابی تنظیمات..."
    
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$SETTINGS_BACKUP_FILE" -C "$TEMP_DIR" || error_exit "خطا در استخراج فایل تنظیمات"
    
    # پشتیبان‌گیری از تنظیمات فعلی
    if [ -f "$INSTALL_DIR/.env" ]; then
        cp "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.backup"
        info "از تنظیمات فعلی پشتیبان گرفته شد: $INSTALL_DIR/.env.backup"
    fi
    
    # کپی تنظیمات جدید
    if [ -f "$TEMP_DIR/.env" ]; then
        cp "$TEMP_DIR/.env" "$INSTALL_DIR/.env"
        success "فایل .env با موفقیت بازیابی شد."
    fi
    
    # در صورت استفاده از Docker، فایل‌های مرتبط را هم کپی می‌کنیم
    if [ "$USE_DOCKER" = true ] && [ -f "$TEMP_DIR/docker-compose.yml" ]; then
        cp "$TEMP_DIR/docker-compose.yml" "$INSTALL_DIR/docker-compose.yml"
        success "فایل docker-compose.yml با موفقیت بازیابی شد."
    fi
    
    # پاک‌سازی فایل‌های موقت
    rm -rf "$TEMP_DIR"
    
    success "تنظیمات با موفقیت بازیابی شدند."
fi

# راه‌اندازی مجدد سرویس
info "در حال راه‌اندازی مجدد سرویس..."

if [ "$USE_DOCKER" = true ]; then
    # استفاده از Docker
    cd "$INSTALL_DIR" || error_exit "دایرکتوری نصب یافت نشد"
    docker-compose restart web || warning "خطا در راه‌اندازی مجدد سرویس"
else
    # نصب مستقیم
    systemctl restart hiroestate 2>/dev/null || warning "خطا در راه‌اندازی مجدد سرویس"
    systemctl restart nginx 2>/dev/null || warning "خطا در راه‌اندازی مجدد سرویس Nginx"
fi

# نمایش اطلاعات تکمیلی
echo ""
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  بازیابی با موفقیت انجام شد  ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "تاریخ و زمان: $(date)"
echo -e "اطلاعات بازیابی شده:"
if [ "$RESTORE_DB" = true ]; then
    echo -e " - دیتابیس: $DB_NAME"
fi
if [ "$RESTORE_MEDIA" = true ]; then
    echo -e " - فایل‌های رسانه در: $INSTALL_DIR/media"
fi
if [ "$RESTORE_SETTINGS" = true ]; then
    echo -e " - تنظیمات در: $INSTALL_DIR/.env"
fi
echo ""
echo -e "سیستم آماده استفاده است!"
echo -e "آدرس سایت: http://localhost (یا دامنه پیکربندی‌شده)"
echo ""
echo -e "توجه: ممکن است نیاز به اجرای مهاجرت‌های دیتابیس داشته باشید:"
if [ "$USE_DOCKER" = true ]; then
    echo -e "$ cd $INSTALL_DIR && docker-compose exec web python manage.py migrate"
else
    echo -e "$ cd $INSTALL_DIR && source venv/bin/activate && python manage.py migrate"
fi
echo ""

exit 0