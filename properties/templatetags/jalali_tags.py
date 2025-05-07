from django import template
import jdatetime
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(value, format_string="%Y/%m/%d"):
    """تبدیل تاریخ میلادی به شمسی"""
    if value is None:
        return ""
    
    try:
        # اگر تاریخ دریافتی به فرمت رشته باشد
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value
        
        # اگر شیء تاریخ باشد
        if isinstance(value, datetime) or isinstance(value, timezone.datetime):
            jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
            return jalali_date.strftime(format_string)
        
        # اگر jdatetime باشد، مستقیماً از آن استفاده می‌کنیم
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return f"{value.year}/{value.month:02d}/{value.day:02d}"
        
        return value
    except Exception:
        # در صورت هر گونه خطا، مقدار اصلی را برمی‌گردانیم
        return str(value)


@register.filter(name='to_jalali_full')
def to_jalali_full(value):
    """تبدیل تاریخ میلادی به شمسی با فرمت کامل"""
    if value is None:
        return ""
    
    # نام ماه‌های شمسی
    jalali_months = {
        1: 'فروردین',
        2: 'اردیبهشت',
        3: 'خرداد',
        4: 'تیر',
        5: 'مرداد',
        6: 'شهریور',
        7: 'مهر',
        8: 'آبان',
        9: 'آذر',
        10: 'دی',
        11: 'بهمن',
        12: 'اسفند'
    }
    
    try:
        # تبدیل تاریخ میلادی به جلالی
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value
        
        if isinstance(value, datetime) or isinstance(value, timezone.datetime):
            jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
            day = jalali_date.day
            month = jalali_months[jalali_date.month]
            year = jalali_date.year
            return f"{day} {month} {year}"
        
        return value
    except Exception:
        return str(value)


@register.filter(name='to_jalali_datetime')
def to_jalali_datetime(value):
    """تبدیل تاریخ و زمان میلادی به شمسی"""
    if value is None:
        return ""
    
    try:
        if isinstance(value, datetime) or isinstance(value, timezone.datetime):
            jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
            return f"{jalali_date.year}/{jalali_date.month:02d}/{jalali_date.day:02d}"
        
        return value
    except Exception:
        return str(value)