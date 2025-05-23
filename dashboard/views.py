from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Max, Min, F, Q
from django.db.models.functions import TruncMonth, TruncDate, ExtractMonth
from properties.models import Property, PropertyStatus, PropertyType, TransactionType
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, datetime
import json
from accounts.decorators import admin_access_required

@admin_access_required
def dashboard_home(request):
    """داشبورد اصلی سیستم با طراحی مدرن و داده‌های پیشرفته"""
    # تعداد کل املاک
    total_properties = Property.objects.count()
    
    # آمار وضعیت املاک
    property_status_stats = Property.objects.values('status__name').annotate(count=Count('id')).order_by('-count')
    
    # محاسبه درصد برای هر آمار
    if total_properties > 0:
        property_status_stats = [
            {
                'status__name': stat['status__name'],
                'count': stat['count'],
                'percentage': (stat['count'] / total_properties) * 100
            } 
            for stat in property_status_stats
        ]
    
    # آمار بر اساس نوع معامله
    transaction_type_stats = Property.objects.values('transaction_type__name').annotate(count=Count('id')).order_by('-count')
    
    # محاسبه درصد برای نوع معامله
    if total_properties > 0:
        transaction_type_stats = [
            {
                'transaction_type__name': stat['transaction_type__name'],
                'count': stat['count'],
                'percentage': (stat['count'] / total_properties) * 100
            } 
            for stat in transaction_type_stats
        ]
    
    # آمار بر اساس نوع ملک
    property_type_stats = Property.objects.values('property_type__name').annotate(count=Count('id')).order_by('-count')
    
    # محاسبه درصد برای نوع ملک
    if total_properties > 0:
        property_type_stats = [
            {
                'property_type__name': stat['property_type__name'],
                'count': stat['count'],
                'percentage': (stat['count'] / total_properties) * 100
            } 
            for stat in property_type_stats
        ]
    
    # میانگین قیمت بر اساس نوع ملک
    avg_price_by_type_raw = Property.objects.values('property_type__name').annotate(avg_price=Avg('price')).order_by('-avg_price')
    
    # تبدیل به فرمت مناسب برای نمایش در قالب
    avg_price_by_type = [
        {
            'property_type__name': item['property_type__name'],
            'avg_price': item['avg_price']
        }
        for item in avg_price_by_type_raw
    ]
    
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
    
    # مدیران و مشاوران فعال
    # کاربرانی که در گروه مدیر املاک یا مشاور املاک هستند
    property_manager_group = Group.objects.filter(name='مدیر املاک').first()
    sales_agent_group = Group.objects.filter(name='مشاور املاک').first()
    
    staff_users_ids = []
    if property_manager_group:
        staff_users_ids.extend(property_manager_group.user_set.values_list('id', flat=True))
    if sales_agent_group:
        staff_users_ids.extend(sales_agent_group.user_set.values_list('id', flat=True))
    
    # حذف تکرارها
    staff_users_ids = list(set(staff_users_ids))
    
    # دریافت کاربران با اطلاعات پروفایل
    staff_users = User.objects.filter(id__in=staff_users_ids).select_related('profile').prefetch_related('properties').order_by('first_name', 'last_name')
    
    # دریافت وضعیت‌های ملک برای مدال‌های تغییر وضعیت
    status_choices = PropertyStatus.objects.all().order_by('name')
    
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
        'staff_users': staff_users,
        'status_choices': status_choices,
        'title': 'داشبورد مدیریت هوشمند'
    }
    
    return render(request, 'dashboard/dashboard.html', context)
