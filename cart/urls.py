from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_cart, name='view_cart'),
    path('add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
    path('add/', views.api_add_to_cart, name='api_add_to_cart'),
    path('update/', views.api_update_cart, name='api_update_cart'),
    path('remove/', views.api_remove_from_cart, name='api_remove_from_cart'),
    path('count/', views.api_cart_count, name='api_cart_count'),
    path('apply-coupon/', views.api_apply_coupon, name='api_apply_coupon'),
]
