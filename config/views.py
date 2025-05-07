from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.management import call_command
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.utils import timezone
import os
import json
import sqlite3
import io
import zipfile
import tempfile
import shutil

from .models import SystemConfig, BackupRecord
from .forms import SystemConfigForm
from properties.models import Property, PropertyType, PropertyStatus, TransactionType

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
