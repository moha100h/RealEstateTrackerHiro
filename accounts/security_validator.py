"""
ماژول اعتبارسنجی امنیت پیشرفته
محافظت پیشرفته در برابر حملات متداول
"""

import re
import logging
import time
import hashlib
import base64
import os
import json
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError

# ثبت لاگ‌های امنیتی
security_logger = logging.getLogger('security')

class SecurityValidators:
    """
    ابزارهای اعتبارسنجی امنیتی قوی برای داده‌های ورودی
    """
    
    @staticmethod
    def validate_safe_string(value, field_name="ورودی", min_length=0, max_length=255):
        """
        اعتبارسنجی رشته‌های ورودی و جلوگیری از انواع تزریق
        
        - حذف محتوای HTML و اسکریپت
        - بررسی طول مجاز
        - اعتبارسنجی ساختاری رشته
        """
        if value is None:
            if min_length > 0:
                raise ValidationError(_(f'{field_name} الزامی است.'))
            return value
            
        # تبدیل به رشته و حذف تگ‌های HTML
        clean_value = str(strip_tags(str(value))).strip()
        
        # بررسی طول
        if len(clean_value) < min_length:
            raise ValidationError(_(f'{field_name} باید حداقل {min_length} کاراکتر داشته باشد.'))
        
        if len(clean_value) > max_length:
            raise ValidationError(_(f'{field_name} نباید بیشتر از {max_length} کاراکتر داشته باشد.'))
        
        # بررسی کاراکترهای خطرناک
        dangerous_patterns = [
            r'<script.*?>.*?</script>', 
            r'javascript:', 
            r'onerror=', 
            r'onload=',
            r'eval\(.*?\)', 
            r'\bSELECT\b.*?\bFROM\b', 
            r'\bUNION\b.*?\bSELECT\b',
            r'\bDROP\b.*?\bTABLE\b',
            r'\bDELETE\b.*?\bFROM\b',
            r'\bINSERT\b.*?\bINTO\b',
            r'\bUPDATE\b.*?\bSET\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                security_logger.warning(f"Potential injection attempt in {field_name}: {value[:50]}...", 
                                      extra={'ip': 'validation', 'user': 'system'})
                raise ValidationError(_(f'{field_name} حاوی محتوای غیرمجاز است.'))
        
        return clean_value
    
    @staticmethod
    def validate_phone_number(value, field_name="شماره تماس"):
        """
        اعتبارسنجی شماره تلفن ایرانی با فرمت‌های مختلف
        """
        if not value:
            return value
            
        # حذف فاصله‌ها و کاراکترهای اضافی
        clean_value = re.sub(r'[\s\-\(\)]+', '', str(value))
        
        # بررسی الگوهای معتبر شماره تلفن
        iran_mobile_pattern = r'^(?:98|\+98|0)?9\d{9}$'  # موبایل ایرانی
        iran_phone_pattern = r'^(?:98|\+98|0)?\d{10}$'  # تلفن ثابت ایرانی
        
        if re.match(iran_mobile_pattern, clean_value) or re.match(iran_phone_pattern, clean_value):
            # استانداردسازی فرمت
            if clean_value.startswith('0'):
                return clean_value
            elif clean_value.startswith('98'):
                return '0' + clean_value[2:]
            elif clean_value.startswith('+98'):
                return '0' + clean_value[3:]
            else:
                return '0' + clean_value
        else:
            raise ValidationError(_(f'{field_name} معتبر نیست.'))
    
    @staticmethod
    def validate_national_code(value, field_name="کد ملی"):
        """
        اعتبارسنجی کد ملی ایرانی
        """
        if not value:
            return value
            
        # حذف فاصله‌ها و کاراکترهای اضافی
        clean_value = re.sub(r'\D', '', str(value))
        
        # بررسی طول
        if len(clean_value) != 10:
            raise ValidationError(_(f'{field_name} باید دقیقاً ۱۰ رقم باشد.'))
        
        # الگوریتم اعتبارسنجی کد ملی
        check = int(clean_value[9])
        s = sum([int(clean_value[i]) * (10 - i) for i in range(9)]) % 11
        
        if (s < 2 and check == s) or (s >= 2 and check == 11 - s):
            return clean_value
        else:
            raise ValidationError(_(f'{field_name} معتبر نیست.'))
    
    @staticmethod
    def validate_postal_code(value, field_name="کد پستی"):
        """
        اعتبارسنجی کد پستی ایرانی ۱۰ رقمی
        """
        if not value:
            return value
            
        # حذف فاصله‌ها و کاراکترهای اضافی
        clean_value = re.sub(r'\D', '', str(value))
        
        # بررسی طول و الگو
        if len(clean_value) != 10 or not clean_value.isdigit():
            raise ValidationError(_(f'{field_name} باید دقیقاً ۱۰ رقم باشد.'))
        
        return clean_value
    
    @staticmethod
    def validate_password_strength(password, field_name="رمز عبور"):
        """
        بررسی قدرت رمز عبور با معیارهای پیشرفته امنیتی
        """
        if not password:
            raise ValidationError(_(f'{field_name} الزامی است.'))
            
        # بررسی طول
        if len(password) < 10:
            raise ValidationError(_(f'{field_name} باید حداقل ۱۰ کاراکتر داشته باشد.'))
            
        # بررسی پیچیدگی
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_(f'{field_name} باید حداقل یک حرف بزرگ انگلیسی داشته باشد.'))
            
        if not re.search(r'[a-z]', password):
            raise ValidationError(_(f'{field_name} باید حداقل یک حرف کوچک انگلیسی داشته باشد.'))
            
        if not re.search(r'\d', password):
            raise ValidationError(_(f'{field_name} باید حداقل یک رقم داشته باشد.'))
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_(f'{field_name} باید حداقل یک کاراکتر خاص (!@#$%^&*) داشته باشد.'))
            
        # بررسی رمزهای متداول
        common_passwords = ['password', '123456789', 'qwerty1234', 'admin1234', '123456789a', 'Aa123456789']
        if password.lower() in common_passwords:
            raise ValidationError(_(f'{field_name} بسیار ساده و قابل حدس است. لطفاً رمز پیچیده‌تری انتخاب کنید.'))
            
        # محاسبه قدرت رمز
        strength = 0
        if len(password) >= 12:
            strength += 1
        if re.search(r'[A-Z].*[A-Z]', password):  # حداقل دو حرف بزرگ
            strength += 1
        if re.search(r'[a-z].*[a-z].*[a-z]', password):  # حداقل سه حرف کوچک
            strength += 1
        if re.search(r'\d.*\d.*\d', password):  # حداقل سه رقم
            strength += 1
        if re.search(r'[!@#$%^&*].*[!@#$%^&*]', password):  # حداقل دو کاراکتر خاص
            strength += 1
            
        if strength < 3:
            raise ValidationError(_(f'{field_name} به اندازه کافی قوی نیست. لطفاً از ترکیب بیشتری از حروف، اعداد و کاراکترهای خاص استفاده کنید.'))
            
        return password
    
    @staticmethod
    def sanitize_filename(filename, max_length=100):
        """
        پاکسازی نام فایل برای جلوگیری از حملات مبتنی بر فایل
        """
        if not filename:
            return None
            
        # حذف مسیرها و کاراکترهای خطرناک
        base_name = os.path.basename(filename)
        
        # حذف کاراکترهای خطرناک
        sanitized = re.sub(r'[^\w\.\-]', '_', base_name)
        
        # محدود کردن طول
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:max_length-len(ext)] + ext
            
        # افزودن پیشوند تصادفی برای جلوگیری از همپوشانی
        random_prefix = hashlib.md5(os.urandom(8)).hexdigest()[:8]
        name, ext = os.path.splitext(sanitized)
        
        return f"{random_prefix}_{name}{ext}"
    
    @staticmethod
    def validate_file_type(file, allowed_types=None, field_name="فایل"):
        """
        اعتبارسنجی نوع فایل با بررسی محتوای واقعی
        """
        if not file:
            return None
            
        if allowed_types is None:
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
            
        # بررسی MIME type واقعی فایل
        try:
            # خواندن bytes ابتدای فایل
            file.seek(0)
            header = file.read(4096)
            file.seek(0)  # برگرداندن به ابتدای فایل
            
            # تشخیص الگوهای معروف فایل
            mime_type = None
            
            # تشخیص الگوهای JPEG
            if header[:3] == b'\xFF\xD8\xFF':
                mime_type = 'image/jpeg'
            # تشخیص الگوهای PNG
            elif header[:8] == b'\x89PNG\r\n\x1A\n':
                mime_type = 'image/png'
            # تشخیص الگوهای GIF
            elif header[:6] in (b'GIF87a', b'GIF89a'):
                mime_type = 'image/gif'
            # تشخیص الگوهای PDF
            elif header[:4] == b'%PDF':
                mime_type = 'application/pdf'
            # تشخیص DOCX
            elif header[:4] == b'PK\x03\x04' and 'word/' in str(header):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            # تشخیص XLSX
            elif header[:4] == b'PK\x03\x04' and 'xl/' in str(header):
                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            # ZIP
            elif header[:4] == b'PK\x03\x04':
                mime_type = 'application/zip'
                
            if mime_type is None:
                raise ValidationError(_(f'نوع {field_name} قابل تشخیص نیست.'))
                
            if mime_type not in allowed_types:
                security_logger.warning(f"Invalid file type: {mime_type} not in {allowed_types}", 
                                     extra={'ip': 'validation', 'user': 'system'})
                raise ValidationError(_(f'نوع {field_name} مجاز نیست. فرمت‌های مجاز: {", ".join(allowed_types)}'))
                
            return file
            
        except Exception as e:
            security_logger.error(f"Error validating file: {str(e)}", 
                               extra={'ip': 'validation', 'user': 'system'})
            raise ValidationError(_(f'خطا در بررسی {field_name}'))
    
    @staticmethod
    def validate_json(data, field_name="داده JSON"):
        """
        اعتبارسنجی ساختار JSON
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_(f'{field_name} ساختار نامعتبری دارد.'))
                
        if not isinstance(data, (dict, list)):
            raise ValidationError(_(f'{field_name} باید یک دیکشنری یا لیست باشد.'))
            
        return data
    
    @staticmethod
    def validate_url(url, allowed_domains=None, field_name="آدرس وب"):
        """
        اعتبارسنجی امن آدرس‌های وب
        """
        if not url:
            return None
            
        # پاکسازی و نرمال‌سازی URL
        url = url.strip()
        
        # بررسی پروتکل امن
        if not (url.startswith('https://') or url.startswith('http://')):
            url = 'https://' + url
            
        # بررسی الگوی کلی URL
        url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(/[-\w%/.]+)*(?:\?[-\w%&=.]*)?(?:#[-\w]*)?$'
        if not re.match(url_pattern, url):
            raise ValidationError(_(f'{field_name} معتبر نیست.'))
            
        # بررسی دامنه‌های مجاز
        if allowed_domains:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if not any(domain.endswith(d) for d in allowed_domains):
                raise ValidationError(_(f'دامنه {domain} مجاز نیست.'))
                
        return url
    
    @staticmethod
    def generate_secure_token(length=32):
        """
        تولید توکن امن برای استفاده در عملیات حساس
        """
        # استفاده از entropy بالا برای تولید توکن
        return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8')[:length]
    
    @staticmethod
    def add_request_metadata(request, data):
        """
        افزودن متادیتای امنیتی به داده‌ها برای ردیابی و تحلیل
        """
        # اطلاعات درخواست
        metadata = {
            'ip': request.META.get('REMOTE_ADDR', '0.0.0.0'),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
            'referer': request.META.get('HTTP_REFERER', 'direct'),
            'timestamp': time.time(),
        }
        
        # اطلاعات کاربر
        if hasattr(request, 'user') and request.user.is_authenticated:
            metadata['user_id'] = request.user.id
            metadata['username'] = request.user.username
            
        if isinstance(data, dict):
            data['_metadata'] = metadata
            return data
        else:
            return metadata

# نمونه استفاده:
# از SecurityValidators.validate_safe_string
# در فرم‌ها یا سریالایزرها برای اعتبارسنجی ورودی‌های کاربر