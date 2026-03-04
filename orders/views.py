from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from cart.models import CartItem
from wallet.models import Wallet
from .models import Order  # <-- correct import

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total = sum([item.total_price() for item in cart_items])
    wallet = Wallet.objects.get(user=request.user)

    if wallet.balance >= total:
        wallet.balance -= total
        wallet.save()
        Order.objects.create(user=request.user, total_amount=total, status='Confirmed')
        cart_items.delete()
        return redirect('home')

    return redirect('view_cart')

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/orders.html', {'orders': user_orders})