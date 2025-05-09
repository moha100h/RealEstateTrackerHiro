from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST

from .models import Property, PropertyType, TransactionType, PropertyStatus
from .forms import PropertyForm
from .filters import PropertyFilter
from config.models import SystemConfig

class PropertyListView(ListView):
    """نمایش لیست املاک"""
    model = Property
    template_name = 'properties/property_list.html'
    context_object_name = 'properties'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # جستجوی سریع در همه فیلدهای مهم
        search_query = self.request.GET.get('search_query', None)
        if search_query:
            queryset = queryset.filter(
                Q(property_code__icontains=search_query) | 
                Q(title__icontains=search_query) | 
                Q(address__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        self.filterset = PropertyFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context['property_statuses'] = PropertyStatus.objects.all()
        return context

class PropertyDetailView(DetailView):
    """نمایش جزئیات ملک"""
    model = Property
    template_name = 'properties/property_detail.html'
    context_object_name = 'property'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['system_config'] = SystemConfig.get_config()
        return context

class PropertyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ایجاد ملک جدید"""
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    success_url = reverse_lazy('properties:property_list')
    
    def test_func(self):
        # فقط ادمین و کاربران با دسترسی مناسب می‌توانند ملک جدید ایجاد کنند
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'ملک با موفقیت اضافه شد.')
        return super().form_valid(form)

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ویرایش ملک"""
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    
    def test_func(self):
        # فقط ادمین و کاربران با دسترسی مناسب می‌توانند ملک را ویرایش کنند
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('properties:property_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'ملک با موفقیت بروزرسانی شد.')
        return super().form_valid(form)

class PropertyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """حذف ملک"""
    model = Property
    template_name = 'properties/property_confirm_delete.html'
    success_url = reverse_lazy('properties:property_list')
    
    def test_func(self):
        # فقط ادمین می‌تواند ملک را حذف کند
        return self.request.user.is_superuser
    
    def get_success_url(self):
        """اضافه کردن پیام موفقیت قبل از هدایت به صفحه لیست املاک"""
        messages.success(self.request, 'ملک با موفقیت حذف شد.')
        return super().get_success_url()

def search_properties(request):
    """جستجوی پیشرفته املاک با فیلترهای متنوع و قالب مدرن"""
    queryset = Property.objects.all().order_by('-created_at')
    
    # پارامترهای جستجو
    query = request.GET.get('query', '')
    transaction_type = request.GET.get('transaction_type', '')
    property_type = request.GET.get('property_type', '')
    status = request.GET.get('status', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_area = request.GET.get('min_area', '')
    max_area = request.GET.get('max_area', '')
    rooms = request.GET.get('rooms', '')
    has_parking = request.GET.get('has_parking', '')
    has_elevator = request.GET.get('has_elevator', '')
    has_storage = request.GET.get('has_storage', '')
    
    # فیلتر کردن بر اساس پارامترها
    if query:
        queryset = queryset.filter(
            Q(property_code__icontains=query) | 
            Q(title__icontains=query) | 
            Q(address__icontains=query) | 
            Q(description__icontains=query)
        )
    
    if transaction_type:
        queryset = queryset.filter(transaction_type_id=transaction_type)
    
    if property_type:
        queryset = queryset.filter(property_type_id=property_type)
    
    if status:
        queryset = queryset.filter(status_id=status)
    
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    
    if max_price:
        queryset = queryset.filter(price__lte=max_price)
    
    if min_area:
        queryset = queryset.filter(area__gte=min_area)
    
    if max_area:
        queryset = queryset.filter(area__lte=max_area)
    
    if rooms:
        queryset = queryset.filter(rooms__gte=rooms)
    
    if has_parking:
        queryset = queryset.filter(has_parking=True)
    
    if has_elevator:
        queryset = queryset.filter(has_elevator=True)
    
    if has_storage:
        queryset = queryset.filter(has_storage=True)
    
    # گرفتن اطلاعات لازم برای فیلترها
    transaction_types = TransactionType.objects.all()
    property_types = PropertyType.objects.all()
    property_statuses = PropertyStatus.objects.all()
    
    # متغیرهای کمکی برای نمایش فیلترهای انتخاب شده
    transaction_type_name = ''
    property_type_name = ''
    status_name = ''
    price_range = ''
    area_range = ''
    
    if transaction_type:
        try:
            transaction_type_obj = TransactionType.objects.get(id=transaction_type)
            transaction_type_name = transaction_type_obj.name
        except:
            pass
            
    if property_type:
        try:
            property_type_obj = PropertyType.objects.get(id=property_type)
            property_type_name = property_type_obj.name
        except:
            pass
            
    if status:
        try:
            status_obj = PropertyStatus.objects.get(id=status)
            status_name = status_obj.name
        except:
            pass
    
    if min_price or max_price:
        min_price_display = f"{int(min_price):,}" if min_price else "0"
        max_price_display = f"{int(max_price):,}" if max_price else "نامحدود"
        price_range = f"{min_price_display} تا {max_price_display} تومان"
    
    if min_area or max_area:
        min_area_display = min_area if min_area else "0"
        max_area_display = max_area if max_area else "نامحدود"
        area_range = f"{min_area_display} تا {max_area_display} متر مربع"
    
    # بررسی وجود هر گونه فیلتر
    has_filters = any([
        query, transaction_type, property_type, status, 
        min_price, max_price, min_area, max_area, 
        rooms, has_parking, has_elevator, has_storage
    ])
    
    # گزارش تعداد املاک پیدا شده برای دیباگ
    print(f"GET params: {request.GET}")
    print(f"Properties found: {queryset.count()}")
    
    context = {
        'properties': queryset,
        'transaction_types': transaction_types,
        'property_types': property_types,
        'property_statuses': property_statuses,
        'has_filters': has_filters,
        'transaction_type_name': transaction_type_name,
        'property_type_name': property_type_name,
        'status_name': status_name,
        'price_range': price_range,
        'area_range': area_range
    }
    
    # استفاده از قالب جدید
    return render(request, 'properties/property_search_advanced.html', context)


@login_required
@require_POST
def change_property_status(request, pk):
    """تغییر وضعیت ملک"""
    # بررسی دسترسی کاربر
    if not request.user.is_staff:
        messages.error(request, 'شما دسترسی لازم برای این عملیات را ندارید.')
        return redirect('dashboard:home')
    
    # دریافت آیدی وضعیت جدید
    try:
        status_id = int(request.POST.get('status_id', 0))
    except ValueError:
        messages.error(request, 'کد وضعیت نامعتبر است.')
        return redirect('dashboard:home')
    
    if status_id <= 0:
        messages.error(request, 'وضعیت مورد نظر انتخاب نشده است.')
        return redirect('dashboard:home')
    
    # دریافت وضعیت جدید
    try:
        new_status = PropertyStatus.objects.get(id=status_id)
    except PropertyStatus.DoesNotExist:
        messages.error(request, 'وضعیت مورد نظر در سیستم یافت نشد.')
        return redirect('dashboard:home')
    
    # پیدا کردن و به‌روزرسانی ملک
    try:
        property_obj = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        messages.error(request, 'ملک مورد نظر یافت نشد.')
        return redirect('dashboard:home')
    
    # ذخیره وضعیت قدیمی برای نمایش در پیام
    old_status = property_obj.status.name
    property_obj.status = new_status
    
    try:
        property_obj.save()
        messages.success(request, f'وضعیت ملک «{property_obj.title}» از «{old_status}» به «{new_status.name}» تغییر یافت.')
    except Exception as e:
        messages.error(request, f'خطا در ذخیره تغییرات: {str(e)}')
        
    # بازگشت به صفحه اصلی داشبورد
    return redirect('dashboard:home')
