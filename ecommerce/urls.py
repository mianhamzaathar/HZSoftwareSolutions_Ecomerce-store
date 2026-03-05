from django.shortcuts import render
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
import store.urls as store_urls
from store import views as store_views

def landing_view(request):
    return render(request, 'landing.html')


urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing page first
    path('', landing_view, name='landing'),
    path('profile/', RedirectView.as_view(pattern_name='store:profile', permanent=False), name='profile'),
    path('wishlist/', RedirectView.as_view(pattern_name='store:wishlist', permanent=False), name='wishlist'),
    path('search/', RedirectView.as_view(pattern_name='store:search', permanent=False), name='search'),

    # Store
    path('store/', include('store.urls')),
    path('store/', include((store_urls.urlpatterns, 'store'), namespace='store')),

    # Accounts
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    # Other apps
    path('cart/', include('cart.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/wishlist/add/', store_views.api_add_to_wishlist, name='api_add_to_wishlist'),
    path('api/wishlist/remove/', store_views.api_remove_from_wishlist, name='api_remove_from_wishlist'),
    path('api/quick-view/<slug:slug>/', store_views.quick_view, name='api_quick_view'),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
