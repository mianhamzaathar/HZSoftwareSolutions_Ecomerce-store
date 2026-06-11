from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Avg

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=80, blank=True, unique=True, null=True)
    seo_title = models.CharField(max_length=120, blank=True)
    seo_description = models.CharField(max_length=255, blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='products/')
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_discount_percentage(self):
        if self.discounted_price and self.discounted_price < self.price:
            return int(((self.price - self.discounted_price) / self.price) * 100)
        return 0

    @property
    def effective_price(self):
        return self.discounted_price or self.price

    @property
    def average_rating(self):
        rating = self.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg']
        return round(rating or 0, 1)

    @property
    def approved_reviews(self):
        return self.reviews.filter(is_approved=True)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.product.name} image"


class ProductVariation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    name = models.CharField(max_length=50, help_text="Example: Size or Color")
    value = models.CharField(max_length=80, help_text="Example: XL or Black")
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('product', 'name', 'value')

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} review by {self.user.username}"


class ShippingZone(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=80, default='Pakistan')
    city = models.CharField(max_length=80, blank=True)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_shipping_minimum = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TaxConfiguration(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tax rate percentage")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"
