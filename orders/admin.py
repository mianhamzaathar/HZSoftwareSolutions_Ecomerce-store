from django.contrib import admin

from .models import CancellationRequest, Invoice, Order, OrderItem, RefundRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'quantity', 'price', 'total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'total_amount', 'status', 'payment_status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('id', 'user__username', 'guest_email', 'tracking_number')
    inlines = [OrderItemInline]


admin.site.register(Invoice)
admin.site.register(RefundRequest)
admin.site.register(CancellationRequest)
