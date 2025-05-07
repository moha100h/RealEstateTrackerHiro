"""
میدل‌ویر‌های سفارشی برای امنیت بیشتر سیستم
"""
import time
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext as _

class RateLimitMiddleware:
    """
    میدل‌ویر محدودیت نرخ درخواست (Rate Limiting)
    برای جلوگیری از حملات DDOS و محدود کردن تعداد درخواست‌های مجاز از یک IP
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # تنظیمات پیش‌فرض اگر در settings.py تعریف نشده باشند
        self.window_size = getattr(settings, 'RATE_LIMIT_MIDDLEWARE', {}).get('WINDOW_SIZE', 60 * 15)  # 15 دقیقه
        self.max_requests = getattr(settings, 'RATE_LIMIT_MIDDLEWARE', {}).get('MAX_REQUESTS', 300)  # حداکثر 300 درخواست
        self.exempt_paths = getattr(settings, 'RATE_LIMIT_MIDDLEWARE', {}).get('EXEMPT_PATHS', ['/static/', '/media/'])
    
    def __call__(self, request):
        # برای مسیرهای استثنا، محدودیت اعمال نمی‌شود
        path = request.path_info
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return self.get_response(request)
        
        # کلید منحصربه‌فرد برای هر IP
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{client_ip}"
        
        # دریافت تاریخچه درخواست‌ها از کش
        requests_history = cache.get(key, [])
        now = time.time()
        
        # تمیز کردن تاریخچه درخواست‌های قدیمی
        requests_history = [t for t in requests_history if t > now - self.window_size]
        
        # بررسی محدودیت
        if len(requests_history) >= self.max_requests:
            return HttpResponse(_('تعداد درخواست‌های شما از حد مجاز بیشتر شده است. لطفاً کمی صبر کنید.'), status=429)
        
        # ثبت درخواست جدید
        requests_history.append(now)
        cache.set(key, requests_history, self.window_size)
        
        # ادامه پردازش درخواست
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """دریافت IP واقعی کاربر با در نظر گرفتن پروکسی‌ها"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AccountLockoutMiddleware:
    """
    میدل‌ویر قفل کردن حساب کاربری بعد از تعداد مشخصی تلاش ناموفق
    برای محدود کردن حملات Brute Force
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # تنظیمات از فایل settings.py
        self.max_attempts = getattr(settings, 'ACCOUNT_LOCKOUT_ATTEMPTS', 5)
        self.lockout_time = getattr(settings, 'ACCOUNT_LOCKOUT_TIME', 30 * 60)  # 30 دقیقه پیش‌فرض
    
    def __call__(self, request):
        # این میدل‌ویر عملاً پس از احراز هویت اجرا می‌شود و فقط برای نمایش پیام استفاده می‌شود
        
        # بررسی می‌کنیم آیا کاربر قفل شده است
        username = request.POST.get('username', '')
        if username and request.path.endswith('/login/'):
            key = f"account_lockout:{username}"
            lockout_data = cache.get(key, {})
            
            if lockout_data.get('locked_until', 0) > time.time():
                # اگر حساب قفل شده است
                remaining_time = int((lockout_data.get('locked_until', 0) - time.time()) / 60)
                return HttpResponse(
                    _(f'حساب کاربری شما به دلیل تلاش‌های ناموفق قفل شده است. لطفاً {remaining_time} دقیقه دیگر تلاش کنید.'),
                    status=403
                )
        
        # ادامه پردازش درخواست
        return self.get_response(request)