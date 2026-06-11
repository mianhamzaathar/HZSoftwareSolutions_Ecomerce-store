from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from cart.models import Cart, CartItem
from store.models import Product, ShippingZone, TaxConfiguration
from wallet.models import Wallet, WalletTransaction
from .models import CancellationRequest, Invoice, Order, OrderItem, RefundRequest


def _cart_items_for_request(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        return list(CartItem.objects.filter(cart=cart).select_related('product')) if cart else []

    guest_cart = request.session.get('guest_cart', {})
    products = Product.objects.filter(id__in=guest_cart.keys(), is_active=True)
    return [
        {
            'product': product,
            'quantity': int(guest_cart.get(str(product.id), 1)),
            'total_price': product.effective_price * int(guest_cart.get(str(product.id), 1)),
        }
        for product in products
    ]


def _item_product(item):
    return item.product if hasattr(item, 'product') else item['product']


def _item_quantity(item):
    return item.quantity if hasattr(item, 'quantity') else item['quantity']


def _calculate_totals(items, request):
    subtotal = sum((_item_product(item).effective_price * _item_quantity(item) for item in items), Decimal('0.00'))
    zone = ShippingZone.objects.filter(is_active=True).order_by('base_rate').first()
    shipping = Decimal('0.00')
    if zone and subtotal and subtotal < zone.free_shipping_minimum:
        shipping = zone.base_rate
    elif subtotal and subtotal < Decimal('5000.00'):
        shipping = Decimal('250.00')

    tax_config = TaxConfiguration.objects.filter(is_active=True, is_default=True).first()
    tax_rate = tax_config.rate if tax_config else Decimal('10.00')
    tax = (subtotal * tax_rate / Decimal('100')).quantize(Decimal('0.01'))

    discount = Decimal('0.00')
    if (request.session.get('coupon') or '').upper() == 'SAVE10':
        discount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))

    return subtotal, shipping, tax, discount, subtotal + shipping + tax - discount


def _create_invoice(order):
    return Invoice.objects.get_or_create(
        order=order,
        defaults={'invoice_number': f'INV-{timezone.now():%Y%m%d}-{order.id:05d}'},
    )[0]


def _notify_order(order, subject='Order update'):
    recipient = order.user.email if order.user else order.guest_email
    if recipient:
        send_mail(
            subject,
            f'Your order #{order.id} status is {order.status}. Total: Rs. {order.total_amount}.',
            None,
            [recipient],
            fail_silently=True,
        )


def checkout(request):
    items = _cart_items_for_request(request)
    if not items:
        messages.error(request, 'Your cart is empty.')
        return redirect('view_cart')

    subtotal, shipping, tax, discount, total = _calculate_totals(items, request)
    zones = ShippingZone.objects.filter(is_active=True)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'wallet')
        shipping_address = request.POST.get('shipping_address') or request.POST.get('address', '')
        if payment_method == 'wallet' and not request.user.is_authenticated:
            messages.error(request, 'Please log in to pay with wallet, or choose another payment method.')
            return redirect('checkout')

        with transaction.atomic():
            for item in items:
                product = _item_product(item)
                quantity = _item_quantity(item)
                if product.stock_quantity < quantity:
                    messages.error(request, f'{product.name} does not have enough stock.')
                    return redirect('view_cart')

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                guest_name=request.POST.get('guest_name', ''),
                guest_email=request.POST.get('guest_email', ''),
                guest_phone=request.POST.get('guest_phone', ''),
                subtotal=subtotal,
                shipping_amount=shipping,
                tax_amount=tax,
                discount_amount=discount,
                total_amount=total,
                payment_method=payment_method,
                payment_status='paid' if payment_method == 'wallet' else 'pending',
                status='Confirmed' if payment_method in ['wallet', 'cod'] else 'Pending',
                shipping_address=shipping_address,
                shipping_zone=request.POST.get('shipping_zone', ''),
            )

            for item in items:
                product = _item_product(item)
                quantity = _item_quantity(item)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    quantity=quantity,
                    price=product.effective_price,
                    total=product.effective_price * quantity,
                )
                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])

            if payment_method == 'wallet':
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                if wallet.balance < total:
                    messages.error(request, 'Wallet balance is not enough for this order.')
                    transaction.set_rollback(True)
                    return redirect('view_cart')
                wallet.balance -= total
                wallet.save(update_fields=['balance'])
                WalletTransaction.objects.create(wallet=wallet, amount=-total, transaction_type='order_payment')

            _create_invoice(order)
            _notify_order(order, 'Your Hamzify order has been placed')

            if request.user.is_authenticated:
                CartItem.objects.filter(cart__user=request.user).delete()
            else:
                request.session['guest_cart'] = {}
            request.session.pop('coupon', None)

        messages.success(request, 'Order placed successfully.')
        if payment_method == 'stripe':
            return redirect(f'/payments/stripe/?order_id={order.id}')
        return redirect('orders')

    return render(request, 'orders/checkout.html', {
        'items': items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'discount': discount,
        'total': total,
        'zones': zones,
    })


@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'orders/orders.html', {
        'orders': user_orders,
        'total_orders': user_orders.count(),
        'pending_count': user_orders.exclude(status__in=['Delivered', 'Cancelled', 'Refunded']).count(),
        'delivered_count': user_orders.filter(status='Delivered').count(),
        'total_spent': user_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST' and order.can_cancel():
        CancellationRequest.objects.get_or_create(
            order=order,
            defaults={'reason': request.POST.get('reason', 'Customer requested cancellation')},
        )
        order.status = 'Cancelled'
        order.save(update_fields=['status', 'updated_at'])
        for item in order.items.select_related('product'):
            if item.product:
                item.product.stock_quantity += item.quantity
                item.product.save(update_fields=['stock_quantity'])
        _notify_order(order, 'Your Hamzify order was cancelled')
        messages.success(request, 'Order cancelled successfully.')
    return redirect('orders')


@login_required
def request_refund(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST' and order.can_refund():
        RefundRequest.objects.create(
            order=order,
            reason=request.POST.get('reason', ''),
            amount=order.total_amount,
        )
        messages.success(request, 'Refund request submitted.')
    return redirect('orders')


@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id, user=request.user)
    invoice = _create_invoice(order)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        response.write('Install reportlab to render PDF invoices.')
        return response

    pdf = canvas.Canvas(response, pagesize=letter)
    y = 750
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(72, y, 'Hamzify Invoice')
    y -= 35
    pdf.setFont('Helvetica', 11)
    for line in [
        f'Invoice: {invoice.invoice_number}',
        f'Order: #{order.id}',
        f'Customer: {order.customer_name}',
        f'Date: {invoice.issued_at:%Y-%m-%d}',
    ]:
        pdf.drawString(72, y, line)
        y -= 20

    y -= 10
    pdf.setFont('Helvetica-Bold', 11)
    pdf.drawString(72, y, 'Item')
    pdf.drawString(380, y, 'Total')
    y -= 18
    pdf.setFont('Helvetica', 10)
    for item in order.items.all():
        pdf.drawString(72, y, f'{item.product_name} x {item.quantity}')
        pdf.drawString(380, y, f'Rs. {item.total}')
        y -= 18

    y -= 15
    for label, value in [
        ('Subtotal', order.subtotal),
        ('Shipping', order.shipping_amount),
        ('Tax', order.tax_amount),
        ('Discount', order.discount_amount),
        ('Total', order.total_amount),
    ]:
        pdf.drawString(300, y, label)
        pdf.drawString(380, y, f'Rs. {value}')
        y -= 18
    pdf.showPage()
    pdf.save()
    return response


@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return JsonResponse({
        'status': order.get_status_display(),
        'estimated_delivery': '2-3 business days',
        'location': order.shipping_zone or 'Warehouse',
        'tracking_number': order.tracking_number,
    })


@staff_member_required
def sales_report(request):
    orders_qs = Order.objects.all()
    stats = {
        'total_sales': orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'orders_count': orders_qs.count(),
        'paid_orders': orders_qs.filter(payment_status='paid').count(),
        'cancelled_orders': orders_qs.filter(status='Cancelled').count(),
    }
    by_status = orders_qs.values('status').annotate(count=Count('id'), total=Sum('total_amount')).order_by('status')
    return render(request, 'orders/sales_report.html', {'stats': stats, 'by_status': by_status})
