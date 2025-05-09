from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Max, Min, F, Q
from django.db.models.functions import TruncMonth, TruncDate, ExtractMonth
from properties.models import Property, PropertyStatus, PropertyType, TransactionType
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
import json

@login_required
def dashboard_home(request):
    """داشبورد اصلی سیستم با طراحی مدرن و داده‌های پیشرفته"""
    # تعداد کل املاک
    total_properties = Property.objects.count()
    
    # آمار وضعیت املاک
    property_status_stats = Property.objects.values('status__name').annotate(count=Count('id')).order_by('-count')
    
    # محاسبه درصد برای هر آمار
    if total_properties > 0:
        property_status_stats = [
            {**stat, 'percentage': (stat['count'] / total_properties) * 100} 
            for stat in property_status_stats
        ]
    
    # آمار بر اساس نوع معامله
    transaction_type_stats = Property.objects.values('transaction_type__name').annotate(count=Count('id')).order_by('-count')
    
    # محاسبه درصد برای نوع معامله
    if total_properties > 0:
        transaction_type_stats = [
            {**stat, 'percentage': (stat['count'] / total_properties) * 100} 
            for stat in transaction_type_stats
        ]
    
    # آمار بر اساس نوع ملک
    property_type_stats = Property.objects.values('property_type__name').annotate(count=Count('id')).order_by('-count')
    
    # محاسبه درصد برای نوع ملک
    if total_properties > 0:
        property_type_stats = [
            {**stat, 'percentage': (stat['count'] / total_properties) * 100} 
            for stat in property_type_stats
        ]
    
    # میانگین قیمت بر اساس نوع ملک
    avg_price_by_type = Property.objects.values('property_type__name').annotate(avg_price=Avg('price')).order_by('-avg_price')
    
    # املاک اخیراً اضافه شده - با اطلاعات کامل برای نمایش در قالب
    recent_properties = Property.objects.select_related('transaction_type', 'property_type', 'status').all().order_by('-created_at')[:5]
    
    # تعداد املاک فروخته شده
    sold_properties = Property.objects.filter(status__name__in=['فروخته شده', 'اجاره داده شده']).count()
    
    # تعداد املاک موجود (قابل معامله)
    available_properties = Property.objects.filter(status__name='موجود').count()
    
    # تعداد املاک در حال ساخت یا آماده تحویل
    upcoming_properties = Property.objects.filter(status__name__in=['در حال ساخت', 'آماده تحویل']).count()
    
    # تعداد املاک رزرو شده
    reserved_properties = Property.objects.filter(status__name='رزرو شده').count()
    
    # آمار افزوده شده در ماه جاری
    now = timezone.now()
    current_month_start = timezone.make_aware(datetime(now.year, now.month, 1))
    current_month_properties = Property.objects.filter(created_at__gte=current_month_start).count()
    
    # نرخ رشد ماهانه (اگر املاک ماه قبل وجود دارد)
    last_month_start = current_month_start - timedelta(days=30)  # تقریبی، کافی برای این مثال
    last_month_properties = Property.objects.filter(
        created_at__gte=last_month_start, 
        created_at__lt=current_month_start
    ).count()
    
    monthly_growth_rate = 0
    if last_month_properties > 0:
        monthly_growth_rate = ((current_month_properties - last_month_properties) / last_month_properties) * 100
    
    # گروه‌بندی قیمت املاک
    price_ranges = {
        'economic': Property.objects.filter(price__lt=1000000000).count(),  # زیر 1 میلیارد تومان
        'mid_range': Property.objects.filter(price__gte=1000000000, price__lt=5000000000).count(),  # 1-5 میلیارد تومان
        'luxury': Property.objects.filter(price__gte=5000000000).count()  # بالای 5 میلیارد تومان
    }
    
    # آمار کلی بروز تنظیم شده
    stats_updated_at = timezone.now()
    
    # جمع مساحت کل املاک (به عنوان یک آمار جالب)
    total_area = Property.objects.aggregate(total=Sum('area'))['total'] or 0
    
    # میانگین روزهای حضور ملک در سیستم تا فروش/اجاره
    # (این مورد نیاز به فیلد 'date_sold' یا مشابه آن دارد که در سیستم فعلی نیست)
    
    context = {
        'property_status_stats': property_status_stats,
        'transaction_type_stats': transaction_type_stats,
        'property_type_stats': property_type_stats,
        'avg_price_by_type': avg_price_by_type,
        'recent_properties': recent_properties,
        'total_properties': total_properties,
        'sold_properties': sold_properties,
        'available_properties': available_properties,
        'upcoming_properties': upcoming_properties,
        'reserved_properties': reserved_properties,
        'current_month_properties': current_month_properties,
        'monthly_growth_rate': monthly_growth_rate,
        'price_ranges': price_ranges,
        'stats_updated_at': stats_updated_at,
        'total_area': total_area,
        'title': 'داشبورد مدیریت هوشمند'
    }
    
    return render(request, 'dashboard/new_dashboard.html', context)
