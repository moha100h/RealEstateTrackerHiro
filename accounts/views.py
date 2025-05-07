from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import UserProfile, create_default_groups
from .forms import CustomAuthenticationForm, UserForm, UserProfileForm
from .decorators import csrf_exempt_class

@csrf_exempt_class
class CustomLoginView(LoginView):
    """نمای سفارشی صفحه ورود"""
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'ورود به سیستم'
        return context
        
    def form_invalid(self, form):
        """در صورت نامعتبر بودن فرم"""
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
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'پروفایل شما با موفقیت بروزرسانی شد.')
            return redirect('accounts:profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'پروفایل کاربری'
    }
    return render(request, 'accounts/profile.html', context)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
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

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ایجاد کاربر جدید - فقط برای مدیران"""
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_superuser or hasattr(self.request.user, 'profile') and self.request.user.profile.is_super_admin
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # ایجاد پروفایل برای کاربر جدید
        UserProfile.objects.create(user=self.object)
        messages.success(self.request, f'کاربر {self.object.username} با موفقیت ایجاد شد.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'افزودن کاربر جدید'
        return context

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ویرایش کاربر - فقط برای مدیران"""
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.is_superuser or hasattr(self.request.user, 'profile') and self.request.user.profile.is_super_admin
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # اطمینان از وجود پروفایل
        UserProfile.objects.get_or_create(user=self.object)
        messages.success(self.request, f'اطلاعات کاربر {self.object.username} با موفقیت بروزرسانی شد.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'ویرایش کاربر {self.object.username}'
        return context

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
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
