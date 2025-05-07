from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.management import call_command
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Q
import os
import json
import sqlite3
import io
import zipfile
import tempfile
import shutil
import pandas as pd
import xlsxwriter
from datetime import datetime

from .models import SystemConfig, BackupRecord
from .forms import SystemConfigForm
from properties.models import Property, PropertyType, PropertyStatus, TransactionType
from accounts.models import User

def is_superuser(user):
    """آیا کاربر، ادمین اصلی سیستم است؟"""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.is_super_admin)

@login_required
@user_passes_test(is_superuser)
def system_config_view(request):
    """نمایش و ویرایش تنظیمات سیستم"""
    config = SystemConfig.get_config()
    
    if request.method == 'POST':
        form = SystemConfigForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات سیستم با موفقیت بروزرسانی شد.')
            return redirect('config:system_config')
    else:
        form = SystemConfigForm(instance=config)
    
    context = {
        'form': form,
        'title': 'تنظیمات سیستم'
    }
    return render(request, 'config/system_config.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_view(request):
    """مدیریت پشتیبان‌گیری و بازیابی سیستم"""
    backups = BackupRecord.objects.all()
    
    context = {
        'backups': backups,
        'title': 'پشتیبان‌گیری و بازیابی'
    }
    return render(request, 'config/backup.html', context)

@login_required
@user_passes_test(is_superuser)
def create_backup(request):
    """ایجاد پشتیبان از پایگاه داده"""
    if request.method == 'POST':
        try:
            # ایجاد فولدر موقت
            temp_dir = tempfile.mkdtemp()
            
            # نام فایل پشتیبان
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{timestamp}"
            backup_path = os.path.join(temp_dir, f"{filename}.json")
            zip_path = os.path.join(temp_dir, f"{filename}.zip")
            
            # استفاده از دستور dumpdata برای ایجاد فایل JSON
            with open(backup_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', '--indent=2', '--exclude=contenttypes', '--exclude=auth.permission', stdout=f)
            
            # ایجاد فایل زیپ
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(backup_path, f"{filename}.json")
            
            # خواندن فایل زیپ برای دانلود
            with open(zip_path, 'rb') as f:
                file_content = f.read()
                
            # ثبت رکورد پشتیبان‌گیری
            backup_record = BackupRecord.objects.create(
                file_name=f"{filename}.zip",
                created_by=request.user,
                file_size=os.path.getsize(zip_path)
            )
            
            # پاکسازی فایل‌های موقت
            shutil.rmtree(temp_dir)
            
            response = HttpResponse(file_content, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
            
            messages.success(request, 'پشتیبان‌گیری با موفقیت انجام شد.')
            return response
            
        except Exception as e:
            messages.error(request, f'خطا در ایجاد پشتیبان: {str(e)}')
    
    return redirect('config:backup')

@login_required
@user_passes_test(is_superuser)
def restore_backup(request):
    """بازیابی پایگاه داده از فایل پشتیبان"""
    if request.method == 'POST' and request.FILES.get('backup_file'):
        try:
            backup_file = request.FILES['backup_file']
            
            # بررسی نوع فایل
            if not backup_file.name.endswith('.zip'):
                messages.error(request, 'فایل پشتیبان باید با فرمت ZIP باشد.')
                return redirect('config:backup')
            
            # ایجاد دایرکتوری موقت
            temp_dir = tempfile.mkdtemp()
            
            # استخراج فایل زیپ
            zip_path = os.path.join(temp_dir, 'backup.zip')
            with open(zip_path, 'wb+') as f:
                for chunk in backup_file.chunks():
                    f.write(chunk)
            
            # باز کردن فایل زیپ
            with zipfile.ZipFile(zip_path, 'r') as zf:
                json_files = [f for f in zf.namelist() if f.endswith('.json')]
                if not json_files:
                    messages.error(request, 'فایل JSON در آرشیو پشتیبان یافت نشد.')
                    return redirect('config:backup')
                
                # استخراج اولین فایل JSON
                json_file = json_files[0]
                zf.extract(json_file, temp_dir)
                
                # بازیابی از فایل JSON
                json_path = os.path.join(temp_dir, json_file)
                call_command('loaddata', json_path)
            
            # پاکسازی فایل‌های موقت
            shutil.rmtree(temp_dir)
            
            messages.success(request, 'بازیابی پشتیبان با موفقیت انجام شد.')
        except Exception as e:
            messages.error(request, f'خطا در بازیابی پشتیبان: {str(e)}')
    else:
        messages.error(request, 'لطفاً یک فایل پشتیبان انتخاب کنید.')
    
    return redirect('config:backup')

@login_required
@user_passes_test(is_superuser)
def export_properties_excel(request):
    """صدور اطلاعات املاک به فرمت اکسل"""
    try:
        # ایجاد فایل اکسل در حافظه
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # فرمت‌های مورد نیاز
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#3F51B5',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
        })
        
        cell_format = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
        })
        
        date_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': 'yyyy/mm/dd',
        })
        
        # فیلدهای لازم برای ورک‌شیت املاک
        property_headers = [
            'شناسه', 'عنوان', 'نوع ملک', 'نوع معامله', 'وضعیت', 'قیمت', 'متراژ', 
            'تعداد اتاق', 'آدرس', 'توضیحات', 'تاریخ ثبت', 'تاریخ آخرین تغییر', 'ثبت کننده'
        ]
        
        # ایجاد ورک‌شیت املاک
        properties_sheet = workbook.add_worksheet('املاک')
        properties_sheet.right_to_left()
        
        # تنظیم عرض ستون‌ها
        properties_sheet.set_column('A:A', 8)  # شناسه
        properties_sheet.set_column('B:B', 30)  # عنوان
        properties_sheet.set_column('C:E', 15)  # نوع ملک، نوع معامله، وضعیت
        properties_sheet.set_column('F:G', 12)  # قیمت و متراژ
        properties_sheet.set_column('H:H', 8)   # تعداد اتاق
        properties_sheet.set_column('I:I', 40)  # آدرس
        properties_sheet.set_column('J:J', 50)  # توضیحات
        properties_sheet.set_column('K:L', 15)  # تاریخ‌ها
        properties_sheet.set_column('M:M', 20)  # ثبت کننده
        
        # نوشتن هدرها
        for col, header in enumerate(property_headers):
            properties_sheet.write(0, col, header, header_format)
        
        # دریافت داده‌های املاک
        properties = Property.objects.all().select_related('property_type', 'transaction_type', 'status', 'created_by')
        
        # نوشتن داده‌ها
        for row, prop in enumerate(properties, start=1):
            properties_sheet.write(row, 0, prop.id, cell_format)
            properties_sheet.write(row, 1, prop.title, cell_format)
            properties_sheet.write(row, 2, prop.property_type.name if prop.property_type else '', cell_format)
            properties_sheet.write(row, 3, prop.transaction_type.name if prop.transaction_type else '', cell_format)
            properties_sheet.write(row, 4, prop.status.name if prop.status else '', cell_format)
            properties_sheet.write(row, 5, prop.price, cell_format)
            properties_sheet.write(row, 6, prop.area, cell_format)
            properties_sheet.write(row, 7, prop.rooms, cell_format)
            properties_sheet.write(row, 8, prop.address, cell_format)
            properties_sheet.write(row, 9, prop.description, cell_format)
            
            created_at = prop.created_at.strftime('%Y/%m/%d') if prop.created_at else ''
            updated_at = prop.updated_at.strftime('%Y/%m/%d') if prop.updated_at else ''
            
            properties_sheet.write(row, 10, created_at, date_format)
            properties_sheet.write(row, 11, updated_at, date_format)
            properties_sheet.write(row, 12, prop.created_by.get_full_name() if prop.created_by else '', cell_format)
        
        # ایجاد ورک‌شیت کاربران
        users_sheet = workbook.add_worksheet('کاربران')
        users_sheet.right_to_left()
        
        # فیلدهای لازم برای ورک‌شیت کاربران
        user_headers = [
            'شناسه', 'نام کاربری', 'نام', 'نام خانوادگی', 'ایمیل', 
            'آخرین ورود', 'وضعیت', 'سِمت', 'شماره تماس'
        ]
        
        # تنظیم عرض ستون‌ها
        users_sheet.set_column('A:A', 8)   # شناسه
        users_sheet.set_column('B:B', 20)  # نام کاربری
        users_sheet.set_column('C:D', 20)  # نام و نام خانوادگی
        users_sheet.set_column('E:E', 30)  # ایمیل
        users_sheet.set_column('F:F', 15)  # آخرین ورود
        users_sheet.set_column('G:G', 10)  # وضعیت
        users_sheet.set_column('H:H', 20)  # سِمت
        users_sheet.set_column('I:I', 15)  # شماره تماس
        
        # نوشتن هدرها
        for col, header in enumerate(user_headers):
            users_sheet.write(0, col, header, header_format)
        
        # دریافت داده‌های کاربران
        users = User.objects.all().select_related('profile')
        
        # نوشتن داده‌ها
        for row, user in enumerate(users, start=1):
            users_sheet.write(row, 0, user.id, cell_format)
            users_sheet.write(row, 1, user.username, cell_format)
            users_sheet.write(row, 2, user.first_name, cell_format)
            users_sheet.write(row, 3, user.last_name, cell_format)
            users_sheet.write(row, 4, user.email, cell_format)
            
            last_login = user.last_login.strftime('%Y/%m/%d %H:%M') if user.last_login else ''
            users_sheet.write(row, 5, last_login, date_format)
            users_sheet.write(row, 6, 'فعال' if user.is_active else 'غیرفعال', cell_format)
            
            # اطلاعات پروفایل
            position = ''
            phone = ''
            if hasattr(user, 'profile'):
                position = user.profile.position or ''
                phone = user.profile.phone or ''
            
            users_sheet.write(row, 7, position, cell_format)
            users_sheet.write(row, 8, phone, cell_format)
        
        # ذخیره و ارسال فایل
        workbook.close()
        output.seek(0)
        
        # تنظیم پاسخ HTTP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hiro_estate_export_{timestamp}.xlsx"
        
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        messages.success(request, 'صدور اطلاعات به فرمت اکسل با موفقیت انجام شد.')
        return response
        
    except Exception as e:
        messages.error(request, f'خطا در صدور اطلاعات به فرمت اکسل: {str(e)}')
        return redirect('config:backup')

@login_required
@user_passes_test(is_superuser)
def export_data_excel(request):
    """صدور داده‌های مهم سیستم به فرمت اکسل"""
    try:
        # ایجاد فایل اکسل در حافظه
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # فرمت‌های مورد نیاز
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#3F51B5',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
        })
        
        cell_format = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'bg_color': '#f5f5f5',
            'border': 1,
        })
        
        # ایجاد صفحه اطلاعات پایه
        info_sheet = workbook.add_worksheet('اطلاعات سیستم')
        info_sheet.right_to_left()
        
        # تنظیم عرض ستون‌ها
        info_sheet.set_column('A:A', 25)
        info_sheet.set_column('B:B', 50)
        
        # اطلاعات پایه سیستم
        info_sheet.merge_range('A1:B1', 'اطلاعات پایه سیستم هوشمند مدیریت املاک هیرو', title_format)
        
        # آمار املاک
        row = 2
        info_sheet.write(row, 0, 'تعداد کل املاک:', cell_format)
        info_sheet.write(row, 1, Property.objects.count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد املاک فروشی:', cell_format)
        info_sheet.write(row, 1, Property.objects.filter(transaction_type__name='فروشی').count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد املاک اجاره‌ای:', cell_format)
        info_sheet.write(row, 1, Property.objects.filter(transaction_type__name='اجاره‌ای').count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد املاک موجود:', cell_format)
        info_sheet.write(row, 1, Property.objects.filter(status__name='موجود').count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد املاک فروخته شده:', cell_format)
        info_sheet.write(row, 1, Property.objects.filter(status__name='فروخته شده').count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد املاک اجاره داده شده:', cell_format)
        info_sheet.write(row, 1, Property.objects.filter(status__name='اجاره داده شده').count(), cell_format)
        
        # آمار کاربران
        row += 2
        info_sheet.merge_range(f'A{row+1}:B{row+1}', 'اطلاعات کاربران سیستم', title_format)
        
        row += 2
        info_sheet.write(row, 0, 'تعداد کل کاربران:', cell_format)
        info_sheet.write(row, 1, User.objects.count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد کاربران فعال:', cell_format)
        info_sheet.write(row, 1, User.objects.filter(is_active=True).count(), cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'تعداد مدیران:', cell_format)
        info_sheet.write(row, 1, User.objects.filter(is_staff=True).count(), cell_format)
        
        # اطلاعات سیستم
        row += 2
        info_sheet.merge_range(f'A{row+1}:B{row+1}', 'تنظیمات سیستم', title_format)
        
        config = SystemConfig.get_config()
        
        row += 2
        info_sheet.write(row, 0, 'عنوان سیستم:', cell_format)
        info_sheet.write(row, 1, config.website_title, cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'نام شرکت/آژانس:', cell_format)
        info_sheet.write(row, 1, config.company_name or '(تنظیم نشده)', cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'آدرس دفتر:', cell_format)
        info_sheet.write(row, 1, config.company_address or '(تنظیم نشده)', cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'شماره تماس:', cell_format)
        info_sheet.write(row, 1, config.company_phone or '(تنظیم نشده)', cell_format)
        
        row += 1
        info_sheet.write(row, 0, 'ایمیل تماس:', cell_format)
        info_sheet.write(row, 1, config.company_email or '(تنظیم نشده)', cell_format)
        
        # صفحه انواع ملک
        property_types_sheet = workbook.add_worksheet('انواع ملک')
        property_types_sheet.right_to_left()
        property_types_sheet.set_column('A:A', 8)
        property_types_sheet.set_column('B:B', 25)
        
        property_types_sheet.write(0, 0, 'شناسه', header_format)
        property_types_sheet.write(0, 1, 'نوع ملک', header_format)
        
        property_types = PropertyType.objects.all()
        for row, ptype in enumerate(property_types, start=1):
            property_types_sheet.write(row, 0, ptype.id, cell_format)
            property_types_sheet.write(row, 1, ptype.name, cell_format)
        
        # صفحه انواع معامله
        transaction_types_sheet = workbook.add_worksheet('انواع معامله')
        transaction_types_sheet.right_to_left()
        transaction_types_sheet.set_column('A:A', 8)
        transaction_types_sheet.set_column('B:B', 25)
        
        transaction_types_sheet.write(0, 0, 'شناسه', header_format)
        transaction_types_sheet.write(0, 1, 'نوع معامله', header_format)
        
        transaction_types = TransactionType.objects.all()
        for row, ttype in enumerate(transaction_types, start=1):
            transaction_types_sheet.write(row, 0, ttype.id, cell_format)
            transaction_types_sheet.write(row, 1, ttype.name, cell_format)
        
        # صفحه وضعیت‌های ملک
        property_statuses_sheet = workbook.add_worksheet('وضعیت‌های ملک')
        property_statuses_sheet.right_to_left()
        property_statuses_sheet.set_column('A:A', 8)
        property_statuses_sheet.set_column('B:B', 25)
        property_statuses_sheet.set_column('C:C', 15)
        
        property_statuses_sheet.write(0, 0, 'شناسه', header_format)
        property_statuses_sheet.write(0, 1, 'وضعیت', header_format)
        property_statuses_sheet.write(0, 2, 'رنگ', header_format)
        
        property_statuses = PropertyStatus.objects.all()
        for row, status in enumerate(property_statuses, start=1):
            property_statuses_sheet.write(row, 0, status.id, cell_format)
            property_statuses_sheet.write(row, 1, status.name, cell_format)
            property_statuses_sheet.write(row, 2, status.color_code or '', cell_format)
        
        # ذخیره و ارسال فایل
        workbook.close()
        output.seek(0)
        
        # تنظیم پاسخ HTTP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hiro_estate_system_data_{timestamp}.xlsx"
        
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        messages.success(request, 'صدور اطلاعات سیستم به فرمت اکسل با موفقیت انجام شد.')
        return response
        
    except Exception as e:
        messages.error(request, f'خطا در صدور اطلاعات سیستم به فرمت اکسل: {str(e)}')
        return redirect('config:backup')
