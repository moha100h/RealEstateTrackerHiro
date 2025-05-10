FROM python:3.11-slim

WORKDIR /app

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# نصب پیش‌نیازهای سیستمی
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    libmagic-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌های پروژه
COPY . /app/

# نصب پیش‌نیازهای پایتون
RUN pip install --upgrade pip && \
    pip install -r project_requirements.md || \
    pip install Django==5.2 dj-database-url==2.3.0 psycopg2-binary==2.9.9 Pillow==11.2.1 \
                python-magic==0.4.27 django-filter==25.1 jdatetime==4.1.1 django-jalali==6.0.1 \
                xlsxwriter==3.2.0 openpyxl==3.1.6 pandas==2.2.1 gunicorn==22.0.0 python-dotenv==1.0.1 \
                whitenoise==6.6.0

# جمع‌آوری فایل‌های استاتیک
RUN python manage.py collectstatic --noinput

# پورت پیش‌فرض
EXPOSE 8000

# اجرای برنامه
CMD ["gunicorn", "hiro_estate.wsgi:application", "--bind", "0.0.0.0:8000"]