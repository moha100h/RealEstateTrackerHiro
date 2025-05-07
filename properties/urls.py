from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.PropertyListView.as_view(), name='property_list'),
    path('search/', views.search_properties, name='property_search'),
    path('create/', views.PropertyCreateView.as_view(), name='property_create'),
    path('detail/<slug:slug>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('update/<slug:slug>/', views.PropertyUpdateView.as_view(), name='property_update'),
    path('delete/<slug:slug>/', views.PropertyDeleteView.as_view(), name='property_delete'),
]
