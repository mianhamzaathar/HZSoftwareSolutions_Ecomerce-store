from django.urls import path
from .views import stripe_payment

urlpatterns = [
    path('stripe/', stripe_payment, name='stripe_payment'),
]