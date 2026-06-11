import json
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product
from .models import Cart, CartItem

def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if not request.user.is_authenticated:
        guest_cart = request.session.get('guest_cart', {})
        guest_cart[str(product.id)] = guest_cart.get(str(product.id), 0) + 1
        request.session['guest_cart'] = guest_cart
        return redirect('view_cart')

    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])
    return redirect('view_cart')

def view_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = list(CartItem.objects.filter(cart=cart).select_related('product', 'product__category'))
    else:
        items = _guest_items(request)

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


def _guest_items(request):
    guest_cart = request.session.get('guest_cart', {})
    products = Product.objects.filter(id__in=guest_cart.keys(), is_active=True).select_related('category')
    items = []
    for product in products:
        quantity = int(guest_cart.get(str(product.id), 1))
        items.append(SimpleNamespace(
            product=product,
            quantity=quantity,
            total_price=lambda p=product, q=quantity: p.effective_price * q,
        ))
    return items


def _guest_count(request):
    return sum(int(q) for q in request.session.get('guest_cart', {}).values())


@require_POST
def api_add_to_cart(request):
    data = _json_body(request)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1) or 1)
    quantity = max(quantity, 1)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    if not request.user.is_authenticated:
        guest_cart = request.session.get('guest_cart', {})
        guest_cart[str(product.id)] = guest_cart.get(str(product.id), 0) + quantity
        request.session['guest_cart'] = guest_cart
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart.',
            'cart_count': _guest_count(request),
        })

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


@require_POST
def api_update_cart(request):
    data = _json_body(request)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1) or 1)

    if not request.user.is_authenticated:
        guest_cart = request.session.get('guest_cart', {})
        if quantity <= 0:
            guest_cart.pop(str(product_id), None)
        else:
            guest_cart[str(product_id)] = quantity
        request.session['guest_cart'] = guest_cart
        return JsonResponse({'success': True, 'cart_count': _guest_count(request)})

    cart, created = Cart.objects.get_or_create(user=request.user)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=['quantity'])

    return JsonResponse({'success': True, 'cart_count': _cart_count(cart)})


@require_POST
def api_remove_from_cart(request):
    data = _json_body(request)
    product_id = data.get('product_id')

    if not request.user.is_authenticated:
        guest_cart = request.session.get('guest_cart', {})
        guest_cart.pop(str(product_id), None)
        request.session['guest_cart'] = guest_cart
        return JsonResponse({'success': True, 'cart_count': _guest_count(request)})

    cart, created = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()

    return JsonResponse({'success': True, 'cart_count': _cart_count(cart)})


def api_cart_count(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': _guest_count(request)})
    cart, created = Cart.objects.get_or_create(user=request.user)
    return JsonResponse({'count': _cart_count(cart)})


@require_POST
def api_apply_coupon(request):
    data = _json_body(request)
    coupon = (data.get('coupon') or '').strip().upper()

    if coupon == 'SAVE10':
        request.session['coupon'] = coupon
        return JsonResponse({'success': True, 'message': 'Coupon applied.'})

    request.session.pop('coupon', None)
    return JsonResponse({'success': False, 'message': 'Invalid coupon code.'}, status=400)
