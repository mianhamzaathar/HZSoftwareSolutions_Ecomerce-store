from django.contrib import admin

from .models import PaymentGateway, PaymentTransaction, PaymentWebhookEvent


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    search_fields = ('name', 'code')


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'gateway', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'gateway', 'currency')
    search_fields = ('reference', 'order__id')


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('gateway_code', 'event_type', 'processed', 'created_at')
    list_filter = ('gateway_code', 'event_type', 'processed')
    search_fields = ('event_id',)
