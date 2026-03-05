import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product
from .models import Cart, CartItem

@login_required
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart).select_related('product', 'product__category')

    subtotal = sum((item.total_price() for item in items), Decimal('0.00'))
    shipping = Decimal('0.00') if subtotal == 0 or subtotal >= Decimal('5000.00') else Decimal('250.00')
    tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))

    coupon = (request.session.get('coupon') or '').upper()
    discount = Decimal('0.00')
    if coupon == 'SAVE10':
        discount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))

    total = subtotal + shipping + tax - discount

    return render(
        request,
        'cart/cart.html',
        {
            'items': items,
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
            'discount': discount,
            'total': total,
        },
    )


def _json_body(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


def _cart_count(cart):
    count = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantity')).get('total')
    return count or 0


@login_required
@require_POST
def api_add_to_cart(request):
    data = _json_body(request)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1) or 1)
    quantity = max(quantity, 1)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        item.quantity = quantity
    else:
        item.quantity += quantity
    item.save(update_fields=['quantity'])

    return JsonResponse({
        'success': True,
        'message': 'Product added to cart.',
        'cart_count': _cart_count(cart),
    })


@login_required
@require_POST
def api_update_cart(request):
    data = _json_body(request)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1) or 1)

    cart, created = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=['quantity'])

    return JsonResponse({'success': True, 'cart_count': _cart_count(cart)})


@login_required
@require_POST
def api_remove_from_cart(request):
    data = _json_body(request)
    product_id = data.get('product_id')

    cart, created = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()

    return JsonResponse({'success': True, 'cart_count': _cart_count(cart)})


@login_required
def api_cart_count(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return JsonResponse({'count': _cart_count(cart)})


@login_required
@require_POST
def api_apply_coupon(request):
    data = _json_body(request)
    coupon = (data.get('coupon') or '').strip().upper()

    if coupon == 'SAVE10':
        request.session['coupon'] = coupon
        return JsonResponse({'success': True, 'message': 'Coupon applied.'})

    request.session.pop('coupon', None)
    return JsonResponse({'success': False, 'message': 'Invalid coupon code.'}, status=400)
