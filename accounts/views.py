import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.core.mail import send_mail
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

from .models import OTPVerification


def _create_otp(user):
    code = f"{random.randint(100000, 999999)}"
    otp = OTPVerification.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_mail(
        'Your Hamzify verification code',
        f'Your OTP code is {code}. It expires in 10 minutes.',
        None,
        [user.email] if user.email else [],
        fail_silently=True,
    )
    return otp


def register(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            _create_otp(user)
            request.session['pending_otp_user_id'] = user.id
            messages.success(request, 'Account created. Please verify the OTP sent to your email.')
            return redirect('verify_otp')
    return render(request, 'accounts/register.html', {'form': form})


def verify_otp(request):
    user_id = request.session.get('pending_otp_user_id')
    if not user_id:
        messages.error(request, 'No OTP verification is pending.')
        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        otp = OTPVerification.objects.filter(user_id=user_id, code=code, is_used=False).order_by('-created_at').first()
        if otp and otp.is_valid():
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            user = otp.user
            login(request, user)
            request.session.pop('pending_otp_user_id', None)
            messages.success(request, 'OTP verified successfully.')
            return redirect('/store/')
        messages.error(request, 'Invalid or expired OTP.')

    return render(request, 'accounts/verify_otp.html')
