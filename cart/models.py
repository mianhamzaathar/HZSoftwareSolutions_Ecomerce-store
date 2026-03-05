from django.contrib.auth.models import User
from django.db import models
from store.models import Product

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def total_price(self):
        unit_price = self.product.discounted_price or self.product.price
        return unit_price * self.quantity
