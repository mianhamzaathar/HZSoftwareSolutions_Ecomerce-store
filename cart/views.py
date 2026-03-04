from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from store.models import Product

@login_required
def add_to_cart(request, slug):
    product = Product.objects.get(slug=slug)
    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    item.quantity += 1
    item.save()
    return redirect('view_cart')

@login_required
def view_cart(request):
    # Get or create the cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get all items in the cart
    items = CartItem.objects.filter(cart=cart)
    
    return render(request, 'cart/cart.html', {'items': items})