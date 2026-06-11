from django.db import models
from django.contrib.auth.models import User
from store.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending','Pending'),
        ('Confirmed','Confirmed'),
        ('Processing','Processing'),
        ('Shipped','Shipped'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),
        ('Refunded','Refunded'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('wallet', 'Wallet'),
        ('stripe', 'Stripe'),
        ('cod', 'Cash on Delivery'),
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    guest_name = models.CharField(max_length=120, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=30, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='wallet')
    shipping_address = models.TextField(blank=True)
    shipping_zone = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id}"

    @property
    def customer_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name or 'Guest'

    def can_cancel(self):
        return self.status in ['Pending', 'Confirmed', 'Processing']

    def can_refund(self):
        return self.payment_status == 'paid' and self.status in ['Confirmed', 'Processing', 'Shipped', 'Delivered']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    variation = models.CharField(max_length=120, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.product_name


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=40, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number


class RefundRequest(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
    reason = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for order #{self.order_id}"


class CancellationRequest(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='cancellation_request')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cancellation for order #{self.order_id}"
