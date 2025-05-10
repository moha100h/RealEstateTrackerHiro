<div dir="rtl">

# راهنمای استقرار سیستم هوشمند مدیریت املاک هیرو (نسخه 2.0)

این راهنما برای استقرار نسخه 2.0 سیستم هوشمند مدیریت املاک هیرو تهیه شده است. برای استقرار می‌توانید از یکی از روش‌های زیر استفاده کنید.

## فهرست مطالب
1. [استقرار با Docker (روش سریع)](#استقرار-با-docker-روش-سریع)
2. [استقرار روی سرور Ubuntu](#استقرار-روی-سرور-ubuntu)
3. [استقرار روی سرویس‌های ابری](#استقرار-روی-سرویس‌های-ابری)
4. [پس از استقرار](#پس-از-استقرار)
5. [مشکلات رایج](#مشکلات-رایج)

## استقرار با Docker (روش سریع)

این روش سریع‌ترین و آسان‌ترین راه برای راه‌اندازی سیستم است.

### پیش‌نیازها
- Docker و Docker Compose نصب شده باشد
- حداقل 2GB RAM و 20GB فضای دیسک

### مراحل استقرار

1. **ایجاد فایل docker-compose.yml**:
```yaml
version: '3'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=hiroestate
      - POSTGRES_USER=hiroestate_user
      - POSTGRES_PASSWORD=strong_password_here
    restart: always

  web:
    image: hiroestate/hiroestate:v2.0
    depends_on:
      - db
    volumes:
      - media_volume:/app/media
      - static_volume:/app/static
    environment:
      - DEBUG=False
      - SECRET_KEY=your_secret_key_here
      - DATABASE_URL=postgres://hiroestate_user:strong_password_here@db:5432/hiroestate
      - ALLOWED_HOSTS=localhost,127.0.0.1,your_domain.com
    restart: always

  nginx:
    image: nginx:1.25
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
      - static_volume:/var/www/html/static
      - media_volume:/var/www/html/media
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

2. **ایجاد پیکربندی Nginx**:
```bash
mkdir -p nginx/conf
```

3. **ایجاد فایل nginx/conf/hiroestate.conf**:
```nginx
server {
    listen 80;
    server_name localhost your_domain.com;
    client_max_body_size 20M;

    location /static/ {
        alias /var/www/html/static/;
    }

    location /media/ {
        alias /var/www/html/media/;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **راه‌اندازی سرویس‌ها**:
```bash
docker-compose up -d
```

5. **ایجاد کاربر ادمین**:
```bash
docker-compose exec web python manage.py create_superuser
```

6. **ایجاد داده‌های اولیه**:
```bash
docker-compose exec web python manage.py create_initial_data
```

## استقرار روی سرور Ubuntu

برای استقرار مستقیم روی سرور Ubuntu، مراحل زیر را دنبال کنید.

### پیش‌نیازها
- سرور Ubuntu 22.04 LTS
- دسترسی SSH به سرور با مجوز root یا sudo
- یک نام دامنه (اختیاری، اما برای SSL توصیه می‌شود)

### مراحل استقرار

1. **به‌روزرسانی سیستم و نصب پیش‌نیازها**:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib libpq-dev supervisor git curl
```

2. برای ادامه مراحل نصب، به بخش "راهنمای نصب و راه‌اندازی سیستم روی سرور Ubuntu" در فایل README.md مراجعه کنید.

## استقرار روی سرویس‌های ابری

### استقرار روی Heroku

1. **نصب Heroku CLI**:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **ورود به حساب Heroku**:
```bash
heroku login
```

3. **ایجاد برنامه جدید**:
```bash
heroku create hiroestate-app
```

4. **افزودن افزونه PostgreSQL**:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

5. **ارسال کد به Heroku**:
```bash
git push heroku main
```

6. **اجرای مهاجرت‌ها**:
```bash
heroku run python manage.py migrate
```

7. **ایجاد کاربر ادمین**:
```bash
heroku run python manage.py create_superuser
```

8. **ایجاد داده‌های اولیه**:
```bash
heroku run python manage.py create_initial_data
```

### استقرار روی Azure App Service

1. **نصب Azure CLI**:
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

2. **ورود به حساب Azure**:
```bash
az login
```

3. **ایجاد گروه منابع**:
```bash
az group create --name HiroEstateGroup --location westeurope
```

4. **ایجاد برنامه App Service**:
```bash
az appservice plan create --name HiroEstatePlan --resource-group HiroEstateGroup --sku B1 --is-linux
```

5. **ایجاد برنامه وب**:
```bash
az webapp create --name hiroestate-app --resource-group HiroEstateGroup --plan HiroEstatePlan --runtime "PYTHON|3.10"
```

6. **ایجاد دیتابیس PostgreSQL**:
```bash
az postgres server create --name hiroestate-db --resource-group HiroEstateGroup --location westeurope --admin-user hiroestate --admin-password StrongPassword123! --sku-name GP_Gen5_2
```

7. **پیکربندی متغیرهای محیطی**:
```bash
az webapp config appsettings set --name hiroestate-app --resource-group HiroEstateGroup --settings DEBUG=False SECRET_KEY=your_secret_key_here DATABASE_URL=postgres://...
```

8. **استقرار از طریق Git**:
```bash
az webapp deployment source config-local-git --name hiroestate-app --resource-group HiroEstateGroup
git remote add azure <git-url-from-previous-command>
git push azure main
```

## پس از استقرار

بعد از استقرار موفق سیستم، مراحل زیر را انجام دهید:

1. **بررسی سلامت سیستم**:
   - دسترسی به صفحه ورود و صفحه اصلی
   - تست فرآیند ورود با کاربر ادمین
   - بررسی دسترسی به پنل مدیریت

2. **تنظیمات امنیتی**:
   - تغییر رمز عبور کاربر ادمین
   - فعال‌سازی HTTPS (در صورت استفاده از دامنه)
   - بررسی دسترسی‌های کاربران

3. **تنظیمات اولیه سیستم**:
   - تنظیم نام و عنوان سایت
   - آپلود لوگوی شرکت
   - تنظیم اطلاعات تماس و پیام‌های پیش‌فرض

4. **پیکربندی پشتیبان‌گیری خودکار**:
   - فعال‌سازی پشتیبان‌گیری روزانه
   - تست فرآیند پشتیبان‌گیری و بازیابی

## مشکلات رایج

### 1. خطای اتصال به دیتابیس
```
راه حل: بررسی تنظیمات DATABASE_URL، اطمینان از دسترسی صحیح به دیتابیس
```

### 2. خطای 500 در صفحات
```
راه حل: بررسی لاگ‌های سیستم با دستور `docker-compose logs web` یا `sudo tail -f /var/log/nginx/error.log`
```

### 3. عدم نمایش استایل و تصاویر
```
راه حل: اطمینان از اجرای دستور collectstatic، بررسی مسیرهای STATIC_URL و MEDIA_URL
```

### 4. خطای دسترسی به فایل‌ها
```
راه حل: بررسی مجوزهای دسترسی با `sudo chown -R hiroestate:hiroestate /var/www/hiroestate`
```

### 5. مشکل در آپلود تصاویر
```
راه حل: بررسی تنظیم client_max_body_size در Nginx، اطمینان از وجود مجوزهای نوشتن در مسیر media
```

برای سؤالات بیشتر می‌توانید به فایل README.md یا مستندات آنلاین مراجعه کنید.

</div>