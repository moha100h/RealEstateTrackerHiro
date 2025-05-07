from .models import SystemConfig

def system_config(request):
    """اضافه کردن تنظیمات سیستم به کل قالب‌ها"""
    config = SystemConfig.get_config()
    return {'system_config': config}
