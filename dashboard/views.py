from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
from properties.models import Property, PropertyStatus, PropertyType, TransactionType
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard_home(request):
    """داشبورد اصلی سیستم"""
    # آمار وضعیت املاک
    property_status_stats = Property.objects.values('status__name').annotate(count=Count('id')).order_by('-count')
    
    # آمار بر اساس نوع معامله
    transaction_type_stats = Property.objects.values('transaction_type__name').annotate(count=Count('id')).order_by('-count')
    
    # آمار بر اساس نوع ملک
    property_type_stats = Property.objects.values('property_type__name').annotate(count=Count('id')).order_by('-count')
    
    # میانگین قیمت بر اساس نوع ملک
    avg_price_by_type = Property.objects.values('property_type__name').annotate(avg_price=Avg('price')).order_by('-avg_price')
    
    # املاک اخیراً اضافه شده
    recent_properties = Property.objects.all().order_by('-created_at')[:5]
    
    # تعداد کل املاک
    total_properties = Property.objects.count()
    
    # تعداد املاک فروخته شده
    sold_properties = Property.objects.filter(status__name__in=['فروخته شده', 'اجاره داده شده']).count()
    
    # تعداد املاک موجود (قابل معامله)
    available_properties = Property.objects.filter(status__name='موجود').count()
    
    context = {
        'property_status_stats': property_status_stats,
        'transaction_type_stats': transaction_type_stats,
        'property_type_stats': property_type_stats,
        'avg_price_by_type': avg_price_by_type,
        'recent_properties': recent_properties,
        'total_properties': total_properties,
        'sold_properties': sold_properties,
        'available_properties': available_properties,
        'title': 'داشبورد مدیریت'
    }
    
    return render(request, 'dashboard/dashboard.html', context)
