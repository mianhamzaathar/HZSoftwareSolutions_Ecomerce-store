from django.shortcuts import render

# Create your views here.
import stripe
from django.shortcuts import redirect

stripe.api_key = "YOUR_SECRET_KEY"

def stripe_payment(request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': 1000,
                'product_data': {'name': 'Order Payment'},
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://127.0.0.1:8000/',
        cancel_url='http://127.0.0.1:8000/cart/',
    )
    return redirect(session.url)