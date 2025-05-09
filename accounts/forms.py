from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User, Group
from .models import UserProfile

class CustomAuthenticationForm(AuthenticationForm):
    """فرم سفارشی ورود به سیستم با طراحی RTL و امنیت بالا"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ و ویژگی‌های امنیتی
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'نام کاربری خود را وارد کنید',
            'autocomplete': 'username',
            'autocapitalize': 'none',
            'spellcheck': 'false',
            'dir': 'rtl'
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'autocomplete': 'current-password',
            'dir': 'rtl'
        })

class UserForm(forms.ModelForm):
    """فرم مدیریت کاربران"""
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='رمز عبور')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False, label='تکرار رمز عبور')
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='گروه‌ها'
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'groups']
        labels = {
            'username': 'نام کاربری',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
            'is_active': 'فعال'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ
        for field_name, field in self.fields.items():
            if field_name != 'groups' and field_name != 'is_active':
                field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            self.add_error('confirm_password', 'رمز عبور و تکرار آن مطابقت ندارند.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # تنظیم رمز عبور اگر وارد شده باشد
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
            # ذخیره گروه‌ها
            self.save_m2m()
            
        return user

class UserProfileEditForm(forms.ModelForm):
    """فرم ویرایش پروفایل کاربر بدون امکان تغییر نام کاربری"""
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label='رمز عبور')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False, label='تکرار رمز عبور')
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            self.add_error('confirm_password', 'رمز عبور و تکرار آن مطابقت ندارند.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # تنظیم رمز عبور اگر وارد شده باشد
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
            
        return user

class UserProfileForm(forms.ModelForm):
    """فرم اطلاعات تکمیلی پروفایل کاربر"""
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'position', 'avatar']
        labels = {
            'phone': 'شماره تلفن',
            'position': 'سِمت',
            'avatar': 'تصویر پروفایل'
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ
        for field_name, field in self.fields.items():
            if field_name != 'avatar':
                field.widget.attrs['class'] = 'form-control'
