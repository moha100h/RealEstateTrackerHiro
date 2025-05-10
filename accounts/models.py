from django.db import models
from django.contrib.auth.models import User, Group

# تعریف گروه‌های دسترسی پیش‌فرض
def create_default_groups():
    """ایجاد گروه‌های پیش‌فرض سیستم با مجوزهای مناسب"""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    from properties.models import Property
    
    # گروه ادمین اصلی با دسترسی کامل به همه بخش‌ها
    main_admin, created = Group.objects.get_or_create(name='admin_super')
    
    # گروه مدیر املاک با دسترسی به مدیریت املاک
    property_manager, created = Group.objects.get_or_create(name='admin_property')
    
    # گروه کارشناس فروش با دسترسی محدود به املاک
    sales_agent, created = Group.objects.get_or_create(name='admin_sales')
    
    # تنظیم مجوزهای هر گروه
    if created or main_admin.permissions.count() == 0:
        # دریافت همه مجوزهای مدیریت کاربران
        user_content_type = ContentType.objects.get_for_model(User)
        user_profile_content_type = ContentType.objects.get_for_model(UserProfile)
        user_permissions = Permission.objects.filter(
            Q(content_type=user_content_type) | 
            Q(content_type=user_profile_content_type)
        )
        main_admin.permissions.add(*user_permissions)
        
        # دریافت همه مجوزهای مدیریت املاک
        property_content_type = ContentType.objects.get_for_model(Property)
        property_permissions = Permission.objects.filter(content_type=property_content_type)
        
        # اضافه کردن مجوزهای مدیریت املاک به هر دو گروه مدیر املاک و ادمین اصلی
        main_admin.permissions.add(*property_permissions)
        property_manager.permissions.add(*property_permissions)
        
        # مجوزهای محدود برای کارشناس فروش
        view_property_permission = Permission.objects.filter(
            content_type=property_content_type, 
            codename__in=['view_property', 'add_property']
        )
        sales_agent.permissions.add(*view_property_permission)
    
    # تنظیم توضیحات فارسی
    group_descriptions = {
        'admin_super': 'مدیر ارشد با دسترسی کامل به سیستم',
        'admin_property': 'مدیر املاک با دسترسی کامل به بخش املاک',
        'admin_sales': 'کارشناس فروش با دسترسی محدود به مشاهده و ثبت ملک'
    }
    
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
