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
    
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
    
    if not isinstance(value, datetime) and not isinstance(value, timezone.datetime):
        return value
    
    # اگر نوع jdatetime باشد، مستقیماً از آن استفاده می‌کنیم
    if hasattr(value, 'togregorian'):
        jalali_date = value
    else:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
    
    return jalali_date.strftime(format_string)


@register.filter(name='to_jalali_full')
def to_jalali_full(value):
    """تبدیل تاریخ میلادی به شمسی با فرمت کامل"""
    if value is None:
        return ""
    
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
    
    if not isinstance(value, datetime) and not isinstance(value, timezone.datetime):
        return value
    
    jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
    
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
    
    day = jalali_date.day
    month = jalali_months[jalali_date.month]
    year = jalali_date.year
    
    return f"{day} {month} {year}"


@register.filter(name='to_jalali_datetime')
def to_jalali_datetime(value):
    """تبدیل تاریخ و زمان میلادی به شمسی"""
    if value is None:
        return ""
    
    if not isinstance(value, datetime) and not isinstance(value, timezone.datetime):
        return value
    
    jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
    return jalali_date.strftime("%Y/%m/%d %H:%M:%S")