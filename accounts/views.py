from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import PermissionDenied
import time

from .models import UserProfile, create_default_groups
from .forms import CustomAuthenticationForm, UserForm, UserProfileForm, UserProfileEditForm
from .mixins import CustomLoginRequiredMixin, AdminRequiredMixin, SuperUserRequiredMixin

class CustomLoginView(LoginView):
    """نمای سفارشی صفحه ورود"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'ورود به سیستم'
        return context
    
    def form_valid(self, form):
        """در صورت معتبر بودن فرم، رکورد تلاش‌های ناموفق را پاک می‌کنیم"""
        username = form.cleaned_data.get('username')
        cache_key = f"account_lockout:{username}"
        cache.delete(cache_key)  # پاک کردن رکورد تلاش‌های ناموفق
        return super().form_valid(form)
        
    def form_invalid(self, form):
        """در صورت نامعتبر بودن فرم"""
        username = form.data.get('username')
        
        if username:
            # بررسی و ثبت تلاش‌های ناموفق
            cache_key = f"account_lockout:{username}"
            lockout_data = cache.get(cache_key, {'attempts': 0})
            
            # اگر حساب قبلاً قفل شده، بررسی می‌کنیم آیا زمان قفل تمام شده
            if 'locked_until' in lockout_data and lockout_data['locked_until'] > time.time():
                # هنوز قفل است
                remaining_time = int((lockout_data['locked_until'] - time.time()) / 60)
                messages.error(
                    self.request, 
                    f'حساب کاربری شما به دلیل تلاش‌های ناموفق قفل شده است. لطفاً {remaining_time} دقیقه دیگر تلاش کنید.'
                )
            else:
                # اگر قفل نیست یا زمان قفل تمام شده، تلاش ناموفق را ثبت می‌کنیم
                max_attempts = getattr(settings, 'ACCOUNT_LOCKOUT_ATTEMPTS', 5)
                lockout_time = getattr(settings, 'ACCOUNT_LOCKOUT_TIME', 30 * 60)
                
                if 'locked_until' in lockout_data and lockout_data['locked_until'] <= time.time():
                    # زمان قفل تمام شده، شمارنده را ریست می‌کنیم
                    lockout_data = {'attempts': 1}
                else:
                    # افزایش شمارنده تلاش‌های ناموفق
                    lockout_data['attempts'] = lockout_data.get('attempts', 0) + 1
                
                # اگر به حد مجاز رسیده، حساب را قفل می‌کنیم
                if lockout_data['attempts'] >= max_attempts:
                    lockout_data['locked_until'] = time.time() + lockout_time
                    messages.error(
                        self.request, 
                        f'حساب کاربری شما به دلیل {max_attempts} تلاش ناموفق به مدت {lockout_time//60} دقیقه قفل شد.'
                    )
                else:
                    # نمایش تعداد تلاش‌های باقی‌مانده
                    remaining_attempts = max_attempts - lockout_data['attempts']
                    messages.warning(
                        self.request,
                        f'نام کاربری یا رمز عبور اشتباه است. {remaining_attempts} تلاش دیگر قبل از قفل شدن حساب باقی مانده است.'
                    )
                
                # ذخیره اطلاعات قفل حساب در کش
                cache.set(cache_key, lockout_data, 24*60*60)  # 24 ساعت نگهداری می‌شود
        
        # اضافه کردن نوع خطا به بافت (context) برای نمایش بهتر در قالب
        return self.render_to_response(self.get_context_data(form=form, error_type='credentials'))

@login_required
def profile_view(request):
    """نمایش و ویرایش پروفایل کاربر"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserProfileEditForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'پروفایل شما با موفقیت بروزرسانی شد.')
            return redirect('accounts:profile')
    else:
        user_form = UserProfileEditForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'پروفایل کاربری'
    }
    return render(request, 'accounts/profile.html', context)

class UserListView(CustomLoginRequiredMixin, UserPassesTestMixin, ListView):
    """لیست کاربران سیستم - فقط برای مدیران"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    
    def test_func(self):
        return self.request.user.is_superuser or hasattr(self.request.user, 'profile') and self.request.user.profile.is_super_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'مدیریت کاربران'
        # ایجاد گروه‌های پیش‌فرض در صورت نیاز
        create_default_groups()
        return context

class UserCreateView(CustomLoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ایجاد کاربر جدید - فقط برای مدیران"""
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_superuser or hasattr(self.request.user, 'profile') and self.request.user.profile.is_super_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'افزودن کاربر جدید'
        # افزودن فرم پروفایل برای آپلود تصویر
        if 'profile_form' not in context:
            context['profile_form'] = UserProfileForm()
        return context
    
    def post(self, request, *args, **kwargs):
        """
        متد بازنویسی شده برای هندل کردن هر دو فرم کاربر و پروفایل
        """
        self.object = None
        user_form = UserForm(request.POST, request=request)
        profile_form = UserProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and (not profile_form.has_changed() or profile_form.is_valid()):
            return self.forms_valid(user_form, profile_form)
        else:
            return self.forms_invalid(user_form, profile_form)
    
    def forms_valid(self, user_form, profile_form):
        """
        متد ذخیره هر دو فرم کاربر و پروفایل
        """
        # ایجاد کاربر جدید
        self.object = user_form.save()
        
        # ایجاد پروفایل برای کاربر جدید
        profile = UserProfile(user=self.object)
        
        # پردازش فرم پروفایل اگر تغییر کرده باشد
        if profile_form.has_changed():
            # کپی کردن داده‌های معتبر از فرم پروفایل به شی پروفایل
            profile.phone = profile_form.cleaned_data.get('phone', '')
            profile.position = profile_form.cleaned_data.get('position', '')
            
            # پردازش آواتار اگر ارسال شده باشد
            avatar_file = profile_form.cleaned_data.get('avatar')
            if avatar_file:
                profile.avatar = avatar_file
                
        # ذخیره پروفایل
        profile.save()
            
        messages.success(self.request, f'کاربر {self.object.username} با موفقیت ایجاد شد.')
        return redirect(self.success_url)
    
    def forms_invalid(self, user_form, profile_form):
        """
        متد پردازش فرم‌های نامعتبر
        """
        context = self.get_context_data(form=user_form, profile_form=profile_form)
        return self.render_to_response(context)

class UserUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ویرایش کاربر - فقط برای مدیران"""
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_superuser or hasattr(self.request.user, 'profile') and self.request.user.profile.is_super_admin
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'ویرایش کاربر {self.object.username}'
        
        # افزودن فرم پروفایل برای آپلود تصویر
        if 'profile_form' not in context:
            # پیدا کردن یا ایجاد پروفایل کاربر
            try:
                profile = self.object.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile(user=self.object)
                profile.save()
                
            context['profile_form'] = UserProfileForm(instance=profile)
            
        return context
        
    def post(self, request, *args, **kwargs):
        """
        متد بازنویسی شده برای هندل کردن هر دو فرم کاربر و پروفایل
        """
        self.object = self.get_object()
        user_form = self.get_form()
        
        # پیدا کردن یا ایجاد پروفایل کاربر
        try:
            profile = self.object.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=self.object)
            profile.save()
            
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and (not profile_form.has_changed() or profile_form.is_valid()):
            return self.forms_valid(user_form, profile_form)
        else:
            return self.forms_invalid(user_form, profile_form)
    
    def forms_valid(self, user_form, profile_form):
        """
        متد ذخیره هر دو فرم کاربر و پروفایل
        """
        # ذخیره کاربر
        self.object = user_form.save()
        
        # ذخیره پروفایل اگر تغییر کرده باشد
        if profile_form.has_changed():
            profile_form.save()
            
        messages.success(self.request, f'اطلاعات کاربر {self.object.username} با موفقیت بروزرسانی شد.')
        return redirect(self.success_url)
    
    def forms_invalid(self, user_form, profile_form):
        """
        متد پردازش فرم‌های نامعتبر
        """
        context = self.get_context_data(form=user_form, profile_form=profile_form)
        return self.render_to_response(context)

class UserDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """حذف کاربر - فقط برای مدیران ارشد"""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        # فقط ادمین اصلی می‌تواند کاربران را حذف کند
        return self.request.user.is_superuser
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(self.request, f'کاربر {user.username} با موفقیت حذف شد.')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'حذف کاربر {self.object.username}'
        return context
