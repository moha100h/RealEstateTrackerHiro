# نیازمندی‌های پروژه سیستم هوشمند مدیریت املاک هیرو

این فایل شامل لیست پکیج‌های مورد نیاز برای پروژه سیستم هوشمند مدیریت املاک هیرو است. از این لیست می‌توانید برای نصب در محیط‌های مختلف استفاده کنید.

## پکیج‌های اصلی

```
Django==5.2
dj-database-url==2.3.0
```

## پایگاه داده

```
psycopg2-binary==2.9.9
```

## مدیریت رسانه

```
Pillow==11.2.1  # برای پردازش تصاویر
python-magic==0.4.27  # برای تشخیص نوع فایل‌ها
```

## فیلترینگ و صفحه‌بندی

```
django-filter==25.1
```

## مدیریت تاریخ شمسی

```
jdatetime==4.1.1
django-jalali==6.0.1
```

## خروجی اکسل و داده

```
xlsxwriter==3.2.0
openpyxl==3.1.6
pandas==2.2.1
```

## امنیت

```
gunicorn==22.0.0
python-dotenv==1.0.1
```

## محیط تولید

```
whitenoise==6.6.0  # برای سرو فایل‌های استاتیک در محیط تولید
```

## ابزارهای توسعه (برای محیط توسعه)

```
black==24.2.0  # فرمت‌دهنده کد
flake8==7.0.0  # آنالیز استاتیک کد
pytest==8.0.1  # تست‌های خودکار
pytest-django==4.8.0  # تست‌های خودکار جنگو
coverage==7.4.1  # پوشش تست
```

## ابزارهای Docker و استقرار

```
environs==11.0.0  # مدیریت متغیرهای محیطی
django-storages==1.14.2  # برای ذخیره‌سازی ابری (S3, Azure, etc.)
boto3==1.34.60  # برای S3 در صورت نیاز
```

## سازگاری

```
typing-extensions==4.13.2
asgiref==3.8.1
sqlparse==0.5.3
```

## نصب با pip

برای نصب همه پکیج‌ها در یک محیط مجازی:

```bash
python -m venv venv
source venv/bin/activate  # برای Linux/Mac
# یا
venv\Scripts\activate  # برای Windows

pip install Django==5.2 dj-database-url==2.3.0 psycopg2-binary==2.9.9 Pillow==11.2.1 python-magic==0.4.27 django-filter==25.1 jdatetime==4.1.1 django-jalali==6.0.1 xlsxwriter==3.2.0 openpyxl==3.1.6 pandas==2.2.1 gunicorn==22.0.0 python-dotenv==1.0.1 whitenoise==6.6.0
```

## نصب با Replit

در Replit می‌توانید از منوی Packages برای نصب پکیج‌ها استفاده کنید یا از دستور زیر در ترمینال:

```bash
pip install Django==5.2 dj-database-url==2.3.0 psycopg2-binary==2.9.9 Pillow==11.2.1 python-magic==0.4.27 django-filter==25.1 jdatetime==4.1.1 django-jalali==6.0.1 xlsxwriter==3.2.0 openpyxl==3.1.6 pandas==2.2.1 gunicorn==22.0.0 python-dotenv==1.0.1 whitenoise==6.6.0
```