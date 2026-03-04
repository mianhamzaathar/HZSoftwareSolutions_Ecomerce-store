from django.urls import path
from .views import checkout, orders

urlpatterns = [
    path('', orders, name='orders'),        # <-- this handles /orders/
    path('checkout/', checkout, name='checkout'),
]