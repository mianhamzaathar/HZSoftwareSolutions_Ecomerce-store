from django.urls import path
from . import views

urlpatterns = [
    path('', views.orders, name='orders'),
    path('checkout/', views.checkout, name='checkout'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('<int:order_id>/refund/', views.request_refund, name='request_refund'),
    path('<int:order_id>/invoice.pdf', views.invoice_pdf, name='invoice_pdf'),
    path('api/track-order/<int:order_id>/', views.track_order, name='track_order'),
    path('admin/sales-report/', views.sales_report, name='sales_report'),
]
