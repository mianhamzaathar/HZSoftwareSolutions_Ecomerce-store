from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    ProductReview,
    ProductVariation,
    ShippingZone,
    TaxConfiguration,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discounted_price', 'stock_quantity', 'is_active', 'is_featured')
    list_filter = ('category', 'is_active', 'is_featured', 'is_new')
    search_fields = ('name', 'sku', 'seo_keywords')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariationInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('product__name', 'user__username', 'comment')


admin.site.register(ShippingZone)
admin.site.register(TaxConfiguration)
