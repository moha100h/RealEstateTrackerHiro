from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q

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
        self.filterset = PropertyFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
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
