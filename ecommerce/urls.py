from django.shortcuts import render
from django.contrib import admin
from django.urls import path, include

def landing_view(request):
    return render(request, 'landing.html')


urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing page first
    path('', landing_view, name='landing'),

    # Store
    path('store/', include('store.urls')),

    # Accounts
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    # Other apps
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
]
