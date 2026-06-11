from django.urls import path
from .views import payment_webhook, stripe_payment

urlpatterns = [
    path('stripe/', stripe_payment, name='stripe_payment'),
    path('webhook/<slug:gateway_code>/', payment_webhook, name='payment_webhook'),
]
