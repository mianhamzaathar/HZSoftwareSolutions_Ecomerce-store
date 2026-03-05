from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),  # shop list
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('api/quick-view/<slug:slug>/', views.quick_view, name='quick_view'),
    path('product/<int:product_id>/add-review/', views.add_review, name='add_review'),
    path('categories/', views.all_categories, name='categories'),
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('cart/', views.cart, name='cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/add-address/', views.add_address, name='add_address'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('search/', views.search, name='search'),
    path('api/wishlist/add/', views.api_add_to_wishlist, name='api_add_to_wishlist'),
    path('api/wishlist/remove/', views.api_remove_from_wishlist, name='api_remove_from_wishlist'),
]
