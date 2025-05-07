from django.db import models
from django.contrib.auth.models import User, Group

# تعریف گروه‌های دسترسی پیش‌فرض
def create_default_groups():
    """ایجاد گروه‌های پیش‌فرض سیستم"""
    # گروه ادمین اصلی
    main_admin, created = Group.objects.get_or_create(name='admin_super')
    
    # گروه مدیر املاک
    property_manager, created = Group.objects.get_or_create(name='admin_property')
    
    # گروه کارشناس فروش
    sales_agent, created = Group.objects.get_or_create(name='admin_sales')
    
    return main_admin, property_manager, sales_agent

class UserProfile(models.Model):
    """پروفایل کاربر برای اطلاعات تکمیلی"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='کاربر')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='شماره تلفن')
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name='سمت')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='تصویر پروفایل')
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل کاربران'
    
    def __str__(self):
        return f"{self.user.username} - {self.user.get_full_name()}"
    
    @property
    def is_super_admin(self):
        """آیا کاربر ادمین اصلی سیستم است؟"""
        return self.user.groups.filter(name='admin_super').exists() or self.user.is_superuser
    
    @property
    def is_property_manager(self):
        """آیا کاربر مدیر املاک است؟"""
        return self.user.groups.filter(name='admin_property').exists()
    
    @property
    def is_sales_agent(self):
        """آیا کاربر کارشناس فروش است؟"""
        return self.user.groups.filter(name='admin_sales').exists()
