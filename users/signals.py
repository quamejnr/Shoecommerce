from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from shop.models import Customer


@receiver(post_save, sender=User)
def create_customer(sender, created, instance, **kwargs):
    # creates a new profile anytime user is a created
    if created:
        Customer.objects.create(user=instance)
        instance.customer.save()
