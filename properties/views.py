from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Property, PropertyType, TransactionType, PropertyStatus
from .forms import PropertyForm
from .filters import PropertyFilter

class PropertyListView(ListView):
    """نمایش لیست املاک"""
    model = Property
    template_name = 'properties/property_list.html'
    context_object_name = 'properties'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # جستجوی سریع در همه فیلدهای مهم
        search_query = self.request.GET.get('property_code', None)  # هنوز نام فیلد property_code است اما در همه فیلدها جستجو می‌کند
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
    slug_url_kwarg = 'slug'

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
        return reverse_lazy('properties:property_detail', kwargs={'slug': self.object.slug})
    
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
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'ملک با موفقیت حذف شد.')
        return super().delete(request, *args, **kwargs)

def search_properties(request):
    """جستجوی پیشرفته املاک"""
    queryset = Property.objects.all()
    property_filter = PropertyFilter(request.GET, queryset=queryset)
    context = {
        'filter': property_filter,
        'properties': property_filter.qs
    }
    return render(request, 'properties/property_search.html', context)


@login_required
@require_POST
def change_property_status(request, pk):
    """تغییر وضعیت ملک"""
    # بررسی دسترسی کاربر
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'شما دسترسی لازم برای این عملیات را ندارید.'
        }, status=403)
    
    # دریافت آیدی وضعیت جدید
    try:
        status_id = int(request.POST.get('status_id'))
        new_status = PropertyStatus.objects.get(id=status_id)
    except (ValueError, PropertyStatus.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'وضعیت مورد نظر یافت نشد.'
        }, status=400)
    
    # پیدا کردن و به‌روزرسانی ملک
    try:
        property = Property.objects.get(pk=pk)
        old_status = property.status.name
        property.status = new_status
        property.save()
        
        # تهیه کلاس CSS برای نمایش وضعیت
        status_class = 'bg-success'
        if new_status.name == 'فروخته شده' or new_status.name == 'اجاره داده شده':
            status_class = 'bg-danger'
        elif new_status.name == 'رزرو شده':
            status_class = 'bg-warning'
        
        return JsonResponse({
            'success': True,
            'message': f'وضعیت ملک از «{old_status}» به «{new_status.name}» تغییر یافت.',
            'status_name': new_status.name,
            'status_class': status_class
        })
    except Property.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'ملک مورد نظر یافت نشد.'
        }, status=404)
