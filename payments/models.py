from django.db import models

from orders.models import Order


class PaymentGateway(models.Model):
    name = models.CharField(max_length=80)
    code = models.SlugField(unique=True)
    public_key = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PaymentTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_transactions')
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='PKR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=150, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gateway} {self.amount} {self.status}"


class PaymentWebhookEvent(models.Model):
    gateway_code = models.CharField(max_length=50)
    event_id = models.CharField(max_length=150, unique=True)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gateway_code}: {self.event_type}"
