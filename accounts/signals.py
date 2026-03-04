from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import UserProfile
from wallet.models import Wallet

def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Wallet.objects.create(user=instance)

post_save.connect(create_profile, sender=User)