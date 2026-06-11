import json

import stripe
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .models import PaymentGateway, PaymentTransaction, PaymentWebhookEvent


def stripe_payment(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None
    gateway = PaymentGateway.objects.filter(code='stripe', is_active=True).first()
    stripe.api_key = gateway.secret_key if gateway else getattr(settings, 'STRIPE_SECRET_KEY', '')

    if not stripe.api_key:
        return redirect('view_cart')

    amount = int((order.total_amount if order else 10) * 100)
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'pkr',
                'unit_amount': amount,
                'product_data': {'name': f'Order #{order.id}' if order else 'Order Payment'},
            },
            'quantity': 1,
        }],
        mode='payment',
        metadata={'order_id': order.id if order else ''},
        success_url=request.build_absolute_uri('/orders/'),
        cancel_url=request.build_absolute_uri('/cart/'),
    )

    if order:
        PaymentTransaction.objects.create(
            order=order,
            gateway=gateway,
            amount=order.total_amount,
            currency='PKR',
            status='pending',
            reference=session.id,
        )
    return redirect(session.url)


@csrf_exempt
def payment_webhook(request, gateway_code):
    raw_payload = request.body
    payload = raw_payload.decode('utf-8')
    gateway = PaymentGateway.objects.filter(code=gateway_code, is_active=True).first()

    if gateway_code == 'stripe':
        webhook_secret = (gateway.webhook_secret if gateway else '') or getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        if webhook_secret:
            signature = request.headers.get('Stripe-Signature', '')
            try:
                data = stripe.Webhook.construct_event(raw_payload, signature, webhook_secret)
            except (ValueError, stripe.SignatureVerificationError):
                return HttpResponseBadRequest('Invalid webhook signature.')
        else:
            data = json.loads(payload or '{}')
    else:
        data = json.loads(payload or '{}')

    event_id = data.get('id', '')
    event_type = data.get('type', 'unknown')

    event, created = PaymentWebhookEvent.objects.get_or_create(
        gateway_code=gateway_code,
        event_id=event_id or f'{gateway_code}-{PaymentWebhookEvent.objects.count() + 1}',
        defaults={'event_type': event_type, 'payload': data},
    )
    if not created:
        return JsonResponse({'received': True, 'duplicate': True})

    order_id = (
        data.get('data', {})
        .get('object', {})
        .get('metadata', {})
        .get('order_id')
    )
    if event_type in ['checkout.session.completed', 'payment_intent.succeeded'] and order_id:
        order = Order.objects.filter(id=order_id).first()
        if order:
            order.payment_status = 'paid'
            order.status = 'Confirmed'
            order.save(update_fields=['payment_status', 'status', 'updated_at'])
            obj = data.get('data', {}).get('object', {})
            references = [value for value in [obj.get('id'), obj.get('payment_intent'), obj.get('client_reference_id')] if value]
            transactions = PaymentTransaction.objects.filter(order=order)
            if references:
                transactions = transactions.filter(reference__in=references)
            transactions.update(status='succeeded', raw_response=data)
            event.processed = True
            event.save(update_fields=['processed'])

    return JsonResponse({'received': True})
