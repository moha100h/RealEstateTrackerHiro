from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.management import call_command
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.db import models
from django.db.models import Q
import django
import os
import sys
import json
import sqlite3
import io
import zipfile
import tempfile
import shutil
import platform
import pandas as pd
import xlsxwriter
import time
import hashlib
from io import StringIO
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
    # اطمینان از این که فقط کاربران مجاز می‌توانند تنظیمات سیستم را مشاهده یا ویرایش کنند
    if not is_superuser(request.user):
        messages.error(request, 'شما مجوز دسترسی به این صفحه را ندارید.')
        return redirect('home')
    
    config = SystemConfig.get_config()
    
    if request.method == 'POST':
        form = SystemConfigForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات سیستم با موفقیت به‌روزرسانی شد.')
            return redirect('config:system_config')
    else:
        form = SystemConfigForm(instance=config)
    
    # اطلاعات آماری برای نمایش
    total_properties = Property.objects.count()
    total_users = User.objects.count()
    
    context = {
        'form': form,
        'title': 'تنظیمات سیستم',
        'config': config,
        'total_properties': total_properties,
        'total_users': total_users,
        
        # اطلاعات اضافی برای قالب
        'color_options': SystemConfig.PRIMARY_COLORS,
        'layout_options': SystemConfig.LAYOUT_STYLES,
        'navbar_options': SystemConfig.NAVBAR_STYLES,
        
        # بخش‌های فعال و غیرفعال
        'has_social_accounts': any([
            config.instagram_url, 
            config.telegram_url, 
            config.whatsapp_number,
            config.linkedin_url,
            config.twitter_url,
            config.facebook_url,
            config.aparat_url,
            config.youtube_url,
        ]),
        'has_contact_info': any([
            config.company_name,
            config.company_address,
            config.company_phone,
            config.company_email,
        ]),
        'has_seo_settings': any([
            config.site_description,
            config.site_keywords,
            config.google_analytics_id,
        ]),
    }
    return render(request, 'config/system_config.html', context)

@login_required
@user_passes_test(is_superuser)
def backup_view(request):
    """مدیریت پشتیبان‌گیری و بازیابی سیستم با امکانات پیشرفته"""
    # بدست آوردن لیست پشتیبان‌ها با مرتب سازی بر اساس جدیدترین
    backups = BackupRecord.objects.all().order_by('-created_at')
    
    # آمار و اطلاعات سیستم
    total_properties = Property.objects.count()
    total_users = User.objects.count()
    total_backups = backups.count()
    
    # دریافت آخرین پشتیبان
    latest_backup = backups.first()
    
    # حجم کل داده‌های پشتیبان
    total_backup_size = sum(backup.file_size for backup in backups)
    total_backup_size_mb = round(total_backup_size / (1024 * 1024), 2) if total_backup_size else 0
    
    # آمار روند پشتیبان‌گیری در ماه‌های اخیر (6 ماه گذشته)
    now = timezone.now()
    six_months_ago = now - timezone.timedelta(days=180)
    backups_by_month = BackupRecord.objects.filter(
        created_at__gte=six_months_ago
    ).extra(
        select={'month': "EXTRACT(month FROM created_at)"}
    ).values('month').annotate(count=models.Count('id')).order_by('month')
    
    context = {
        'backups': backups,
        'title': 'پشتیبان‌گیری و بازیابی',
        'total_properties': total_properties,
        'total_users': total_users,
        'total_backups': total_backups,
        'latest_backup': latest_backup,
        'total_backup_size_mb': total_backup_size_mb,
        'backups_by_month': list(backups_by_month),
    }
    return render(request, 'config/backup.html', context)

@login_required
@user_passes_test(is_superuser)
def create_backup(request):
    """ایجاد پشتیبان از پایگاه داده و فایل‌های مدیا با امکانات پیشرفته"""
    # Verify that the user still has permission to create backup
    if not is_superuser(request.user):
        messages.error(request, 'شما مجوز دسترسی به این عملیات را ندارید.')
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        try:
            # محدود کردن تعداد عملیات پشتیبان‌گیری با منطق پیشرفته
            last_hour_backups = BackupRecord.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(hours=1),
                created_by=request.user
            ).count()
            
            if last_hour_backups >= 5:
                messages.warning(
                    request, 
                    'شما در یک ساعت گذشته بیش از حد مجاز (5 بار) پشتیبان‌گیری کرده‌اید. لطفاً کمی صبر کنید.'
                )
                return redirect('config:backup')
            
            # بررسی وضعیت دیسک و فضای کافی
            _, _, free = shutil.disk_usage("/")
            min_required_space = 500 * 1024 * 1024  # 500 MB
            if free < min_required_space:
                messages.error(
                    request,
                    f'فضای دیسک کافی برای پشتیبان‌گیری موجود نیست. حداقل 500 مگابایت فضای آزاد مورد نیاز است.'
                )
                return redirect('config:backup')
            
            # ایجاد فولدر موقت با مجوز محدود و امنیت بالا
            temp_dir = tempfile.mkdtemp(prefix='hiro_backup_')
            os.chmod(temp_dir, 0o700)  # فقط کاربر فعلی دسترسی داشته باشد
            
            # نام فایل پشتیبان به همراه تایم استمپ امن
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            safe_username = ''.join(c for c in request.user.username if c.isalnum())[:20]
            filename = f"backup_{safe_username}_{timestamp}"
            backup_path = os.path.join(temp_dir, f"{filename}.json")
            media_dir = os.path.join(temp_dir, 'media')
            zip_path = os.path.join(temp_dir, f"{filename}.zip")
            
            # استفاده از دستور dumpdata برای ایجاد فایل JSON با محدودیت حجم و فیلتر پیشرفته
            with open(backup_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', '--indent=2', 
                            '--exclude=contenttypes', 
                            '--exclude=auth.permission', 
                            '--exclude=admin.logentry', 
                            '--exclude=sessions.session',
                            '--natural-foreign',  # استفاده از کلیدهای طبیعی برای روابط خارجی
                            stdout=f)
            
            # ذخیره فایل مانیفست با اطلاعات سیستم
            manifest = {
                'created_at': timezone.now().isoformat(),
                'created_by': request.user.username,
                'django_version': django.get_version(),
                'system_info': {
                    'python_version': sys.version,
                    'platform': platform.platform(),
                    'hostname': platform.node()
                },
                'app_version': getattr(settings, 'APP_VERSION', '1.0.0'),
                'total_properties': Property.objects.count(),
                'total_users': User.objects.count()
            }
            
            manifest_path = os.path.join(temp_dir, 'manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            # کپی کردن فایل‌های مدیا با بهینه‌سازی و حفظ متادیتا
            media_source = os.path.join(settings.BASE_DIR, 'media')
            if os.path.exists(media_source):
                # ایجاد دایرکتوری مدیا در فولدر موقت
                os.makedirs(media_dir, exist_ok=True)
                
                # لیست فایل‌های مورد نیاز برای پشتیبان‌گیری
                for root, dirs, files in os.walk(media_source):
                    for directory in dirs:
                        source_dir = os.path.join(root, directory)
                        # مسیر نسبی نسبت به دایرکتوری media
                        relative_path = os.path.relpath(source_dir, media_source)
                        target_dir = os.path.join(media_dir, relative_path)
                        os.makedirs(target_dir, exist_ok=True)
                    
                    for file in files:
                        source_file = os.path.join(root, file)
                        # مسیر نسبی نسبت به دایرکتوری media
                        relative_path = os.path.relpath(os.path.join(root, file), media_source)
                        target_file = os.path.join(media_dir, relative_path)
                        # اطمینان از وجود دایرکتوری مقصد
                        os.makedirs(os.path.dirname(target_file), exist_ok=True)
                        # کپی فایل با حفظ متادیتا
                        shutil.copy2(source_file, target_file)
            
            # ایجاد فایل زیپ با سطح فشرده‌سازی بالا
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                # افزودن فایل JSON
                zf.write(backup_path, f"{filename}.json")
                
                # افزودن مانیفست
                zf.write(manifest_path, 'manifest.json')
                
                # افزودن فایل‌های مدیا با فیلتر و پیشرفت‌نما
                if os.path.exists(media_dir):
                    for root, dirs, files in os.walk(media_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # مسیر نسبی برای ذخیره در زیپ
                            arcname = os.path.join('media', os.path.relpath(file_path, media_dir))
                            # بررسی پسوند فایل برای جلوگیری از افزودن فایل‌های موقتی
                            if not (file.endswith('.tmp') or file.endswith('.temp')):
                                zf.write(file_path, arcname)
            
            # رمزنگاری فایل ZIP (اختیاری)
            # در نسخه‌های آینده می‌توان از رمزنگاری استفاده کرد
            
            # خواندن فایل زیپ برای دانلود
            with open(zip_path, 'rb') as f:
                file_content = f.read()
                
            # محاسبه چک‌سام فایل نهایی
            file_checksum = hashlib.sha256()
            with open(zip_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    file_checksum.update(chunk)
            checksum_hex = file_checksum.hexdigest()
            
            # دریافت نوع و توضیحات پشتیبان از فرم
            backup_description = request.POST.get('description', '')
            backup_type = request.POST.get('backup_type', 'full')
            compression_level = int(request.POST.get('compression_level', '9'))
            
            # تعیین نوع پشتیبان بر اساس محتوا
            if not os.path.exists(media_dir):
                backup_type = 'data_only'  # اگر مدیا نداشته باشد
            
            # ثبت رکورد پشتیبان‌گیری با اطلاعات تکمیلی
            file_size = os.path.getsize(zip_path)
            backup_record = BackupRecord.objects.create(
                file_name=f"{filename}.zip",
                created_by=request.user,
                file_size=file_size,
                backup_type=backup_type,
                description=backup_description or f"پشتیبان سیستم شامل {Property.objects.count()} ملک و {User.objects.count()} کاربر",
                checksum=checksum_hex,
                compression_level=compression_level
            )
            
            # پاکسازی فایل‌های موقت
            shutil.rmtree(temp_dir)
            
            response = HttpResponse(file_content, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
            
            # افزودن هدرهای امنیتی
            response['X-Content-Type-Options'] = 'nosniff'
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            
            messages.success(request, 'پشتیبان‌گیری با موفقیت انجام شد.')
            return response
            
        except Exception as e:
            # ثبت خطا با جزئیات بیشتر برای عیب‌یابی
            error_msg = f'خطا در ایجاد پشتیبان: {str(e)}'
            print(f"Backup error: {str(e)}", file=sys.stderr)
            
            # پاکسازی فایل‌های موقت در صورت وجود
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
            messages.error(request, error_msg)
    
    return redirect('config:backup')

@login_required
@user_passes_test(is_superuser)
def restore_backup(request):
    """بازیابی پایگاه داده و فایل‌های مدیا از فایل پشتیبان با امکانات پیشرفته"""
    # Verify that the user still has permission to restore backup
    if not is_superuser(request.user):
        messages.error(request, 'شما مجوز دسترسی به این عملیات را ندارید.')
        return redirect('dashboard:home')
        
    if request.method == 'POST' and request.FILES.get('backup_file'):
        temp_dir = None
        try:
            backup_file = request.FILES['backup_file']
            
            # بررسی نوع فایل با روش‌های چندگانه (مجیک بایت، پسوند، هدر)
            if not backup_file.name.endswith('.zip'):
                messages.error(request, 'فایل پشتیبان باید با فرمت ZIP باشد.')
                return redirect('config:backup')
            
            # بررسی محتوای ابتدای فایل (مجیک بایت‌های ZIP)
            file_header = backup_file.read(4)
            backup_file.seek(0)  # برگشت به ابتدای فایل
            if file_header != b'PK\x03\x04':
                messages.error(request, 'فایل انتخاب شده یک فایل ZIP معتبر نیست.')
                return redirect('config:backup')
                
            # محدودیت اندازه فایل (200 مگابایت)
            max_file_size = 200 * 1024 * 1024  # 200 MB
            if backup_file.size > max_file_size:
                messages.error(request, 'حجم فایل پشتیبان بیشتر از حد مجاز (200 مگابایت) است.')
                return redirect('config:backup')
            
            # بررسی فضای دیسک
            _, _, free = shutil.disk_usage("/")
            required_space = backup_file.size * 2  # حداقل دو برابر حجم فایل زیپ
            if free < required_space:
                messages.error(
                    request,
                    f'فضای دیسک کافی برای بازیابی پشتیبان موجود نیست. حداقل {required_space / (1024*1024):.1f} مگابایت فضای آزاد مورد نیاز است.'
                )
                return redirect('config:backup')
            
            # ایجاد دایرکتوری موقت با دسترسی محدود و امنیت بالا
            temp_dir = tempfile.mkdtemp(prefix='hiro_restore_')
            os.chmod(temp_dir, 0o700)  # فقط کاربر فعلی دسترسی داشته باشد
            
            # استخراج فایل زیپ با کنترل حجم و محتوا
            zip_path = os.path.join(temp_dir, 'backup.zip')
            with open(zip_path, 'wb+') as f:
                # استفاده از chunks برای جلوگیری از مصرف زیاد حافظه
                file_size = 0
                for chunk in backup_file.chunks():
                    file_size += len(chunk)
                    if file_size > max_file_size:  # بررسی مجدد حجم فایل حین پردازش
                        f.close()
                        os.unlink(zip_path)
                        messages.error(request, 'حجم فایل پشتیبان بیشتر از حد مجاز است.')
                        return redirect('config:backup')
                    f.write(chunk)
            
            # زمان شروع عملیات استخراج برای اندازه‌گیری عملکرد
            start_time = time.time()
            
            # باز کردن فایل زیپ
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # بررسی محتوای فایل پشتیبان
                all_files = zf.namelist()
                json_files = [f for f in all_files if f.endswith('.json') and not f.startswith('manifest')]
                media_files = [f for f in all_files if f.startswith('media/')]
                manifest_file = 'manifest.json' if 'manifest.json' in all_files else None
                
                # بررسی مانیفست (اگر وجود داشته باشد)
                manifest_data = {}
                if manifest_file:
                    zf.extract(manifest_file, temp_dir)
                    manifest_path = os.path.join(temp_dir, manifest_file)
                    
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest_data = json.load(f)
                            
                        # نمایش اطلاعات مانیفست به کاربر
                        if 'created_at' in manifest_data:
                            created_time = datetime.fromisoformat(manifest_data['created_at']).strftime('%Y-%m-%d %H:%M')
                            messages.info(request, f'تاریخ ایجاد پشتیبان: {created_time}')
                        
                        if 'total_properties' in manifest_data and 'total_users' in manifest_data:
                            messages.info(
                                request, 
                                f'اطلاعات پشتیبان: {manifest_data["total_properties"]} ملک و {manifest_data["total_users"]} کاربر'
                            )
                    except json.JSONDecodeError:
                        messages.warning(request, 'فایل مانیفست پشتیبان آسیب دیده است، اما بازیابی ادامه می‌یابد.')
                
                if not json_files:
                    messages.error(request, 'فایل JSON در آرشیو پشتیبان یافت نشد.')
                    return redirect('config:backup')
                
                # استخراج اولین فایل JSON (داده‌های اصلی)
                json_file = json_files[0]
                zf.extract(json_file, temp_dir)
                
                # بازیابی از فایل JSON با محافظت از خطا
                json_path = os.path.join(temp_dir, json_file)
                
                # بررسی اعتبار فایل JSON قبل از بازیابی
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json.load(f)  # تلاش برای بارگذاری JSON برای اطمینان از اعتبار آن
                except json.JSONDecodeError:
                    messages.error(request, 'فایل JSON معتبر نیست و ممکن است آسیب دیده باشد.')
                    return redirect('config:backup')
                    
                # اجرای دستور بازیابی با محافظت از خطا
                restore_result = StringIO()
                call_command('loaddata', json_path, stdout=restore_result)
                
                # نمایش نتیجه بازیابی
                restore_output = restore_result.getvalue()
                if "Installed" in restore_output:
                    installed_count = restore_output.count("Installed")
                    messages.success(request, f'{installed_count} رکورد از دیتابیس با موفقیت بازیابی شد.')
                
                # بازیابی فایل‌های مدیا با گزینه‌های پیشرفته
                if media_files:
                    media_dir = os.path.join(settings.BASE_DIR, 'media')
                    
                    # فقط در صورت انتخاب گزینه‌ی حذف فایل‌های قبلی
                    clean_media = request.POST.get('clean_media', 'on') == 'on'
                    if clean_media and os.path.exists(media_dir):
                        # به جای حذف کامل، پوشه‌ها را یکی یکی بررسی و پاک می‌کنیم
                        files_removed = 0
                        for root, dirs, files in os.walk(media_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                if os.path.isfile(file_path):
                                    try:
                                        os.unlink(file_path)
                                        files_removed += 1
                                    except (OSError, PermissionError):
                                        # اگر فایل در حال استفاده است، آن را نادیده می‌گیریم
                                        continue
                        
                        if files_removed > 0:
                            messages.info(request, f'{files_removed} فایل مدیا قبلی حذف شد.')
                    else:
                        # ایجاد دایرکتوری مدیا اگر وجود ندارد
                        os.makedirs(media_dir, exist_ok=True)
                    
                    # استخراج فایل‌های مدیا با مکانیزم امنیتی و گزارش پیشرفت
                    files_extracted = 0
                    files_skipped = 0
                    
                    for file in media_files:
                        # حذف 'media/' از ابتدای مسیر
                        relative_path = file[6:] if file.startswith('media/') else file
                        
                        # محافظت در برابر حملات Path Traversal
                        if relative_path and '..' not in relative_path and not relative_path.startswith('/'):
                            # فیلتر کردن کاراکترهای غیرمجاز
                            safe_path = ''.join(c for c in relative_path if c.isalnum() or c in '._-/() ')
                            
                            # مسیر کامل فایل
                            file_path = os.path.normpath(os.path.join(media_dir, safe_path))
                            
                            # اطمینان از اینکه هنوز داخل دایرکتوری مدیا هستیم (جلوگیری از Path Traversal)
                            if os.path.commonpath([media_dir]) == os.path.commonpath([media_dir, file_path]):
                                # اطمینان از وجود دایرکتوری مقصد
                                try:
                                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                    
                                    # بررسی پسوند فایل برای فیلتر کردن فایل‌های غیرمجاز
                                    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.svg',
                                                               '.doc', '.docx', '.xls', '.xlsx', '.mp4', '.avi',
                                                               '.mov', '.mp3', '.wav', '.zip')):
                                        # استخراج فایل مدیا با محدودیت اندازه
                                        source = zf.open(file)
                                        with open(file_path, 'wb') as target:
                                            # محدودیت اندازه هر فایل به 20 مگابایت
                                            shutil.copyfileobj(source, target, 20 * 1024 * 1024)
                                        files_extracted += 1
                                    else:
                                        files_skipped += 1
                                except (OSError, IOError) as e:
                                    # ثبت رویداد خطا بدون توقف فرآیند
                                    print(f"Error extracting file {file}: {str(e)}", file=sys.stderr)
                                    files_skipped += 1
                                    continue
                    
                    # گزارش نتیجه استخراج فایل‌ها
                    messages.success(request, f'{files_extracted} فایل مدیا با موفقیت بازیابی شد.')
                    if files_skipped > 0:
                        messages.warning(request, f'{files_skipped} فایل به دلیل مشکلات امنیتی یا دسترسی نادیده گرفته شد.')
            
            # گزارش زمان انجام عملیات
            elapsed_time = time.time() - start_time
            messages.info(request, f'عملیات بازیابی در {elapsed_time:.2f} ثانیه انجام شد.')
            
            # پاکسازی فایل‌های موقت
            shutil.rmtree(temp_dir)
            
            # ثبت رکورد بازیابی
            restore_log = f"بازیابی از فایل {backup_file.name} - {len(json_files)} فایل JSON و {len(media_files)} فایل مدیا"
            
            messages.success(request, 'بازیابی پشتیبان با موفقیت انجام شد.')
        except zipfile.BadZipFile:
            messages.error(request, 'فایل ZIP معتبر نیست یا آسیب دیده است.')
        except Exception as e:
            error_msg = f'خطا در بازیابی پشتیبان: {str(e)}'
            print(f"Restore error: {str(e)}", file=sys.stderr)
            messages.error(request, error_msg)
        finally:
            # اطمینان از پاکسازی فایل‌های موقت در هر شرایطی
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    else:
        messages.error(request, 'لطفاً یک فایل پشتیبان انتخاب کنید.')
    
    return redirect('config:backup')

@login_required
@user_passes_test(is_superuser)
def export_properties_excel(request):
    """صدور اطلاعات املاک به فرمت اکسل"""
    # Verify that the user still has permission to export data
    if not is_superuser(request.user):
        messages.error(request, 'شما مجوز دسترسی به این عملیات را ندارید.')
        return redirect('dashboard:home')
        
    try:
        # ایجاد فایل اکسل در حافظه با پردازش ایمن
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'constant_memory': True})
        
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
        
        # دریافت داده‌های املاک با استفاده از تکنیک‌های بهینه‌سازی برای کاهش حجم مصرفی حافظه
        # محدود کردن تعداد رکوردها برای جلوگیری از مشکلات امنیتی مرتبط با حافظه
        properties = Property.objects.all().select_related(
            'property_type', 'transaction_type', 'status', 'document_type'
        ).order_by('-updated_at')[:5000]  # محدود کردن رکوردها به 5000 تا
        
        # نوشتن داده‌ها با محافظت از مشکلات امنیتی مرتبط با محتوای فایل
        for row, prop in enumerate(properties, start=1):
            # محافظت از فیلدها با sanitization
            properties_sheet.write(row, 0, prop.id, cell_format)
            properties_sheet.write(row, 1, str(prop.title)[:255] if prop.title else '', cell_format)  # محدودیت طول فیلد
            properties_sheet.write(row, 2, str(prop.property_type.name)[:50] if prop.property_type else '', cell_format)
            properties_sheet.write(row, 3, str(prop.transaction_type.name)[:50] if prop.transaction_type else '', cell_format)
            properties_sheet.write(row, 4, str(prop.status.name)[:50] if prop.status else '', cell_format)
            properties_sheet.write(row, 5, prop.price, cell_format)
            properties_sheet.write(row, 6, prop.area, cell_format)
            properties_sheet.write(row, 7, prop.rooms, cell_format)
            properties_sheet.write(row, 8, str(prop.address)[:500] if prop.address else '', cell_format)  # محدود کردن طول آدرس
            properties_sheet.write(row, 9, str(prop.description)[:1000] if prop.description else '', cell_format)  # محدود کردن طول توضیحات
            
            created_at = prop.created_at.strftime('%Y/%m/%d') if prop.created_at else ''
            updated_at = prop.updated_at.strftime('%Y/%m/%d') if prop.updated_at else ''
            
            properties_sheet.write(row, 10, created_at, date_format)
            properties_sheet.write(row, 11, updated_at, date_format)
            properties_sheet.write(row, 12, '', cell_format)  # فیلد ثبت کننده در حال حاضر در مدل Property وجود ندارد
        
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
    # Verify that the user still has permission to export data
    if not is_superuser(request.user):
        messages.error(request, 'شما مجوز دسترسی به این عملیات را ندارید.')
        return redirect('dashboard:home')
        
    try:
        # ایجاد فایل اکسل در حافظه با تنظیمات امنیتی مناسب
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'constant_memory': True})
        
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
