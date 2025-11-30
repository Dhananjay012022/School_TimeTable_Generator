from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensure every User has a related UserProfile.
    """
    if created:
        # New user -> create profile
        UserProfile.objects.create(user=instance)
    else:
        # Existing user -> just save the profile if it exists
        # (if it doesn't exist for some reason, create it)
        UserProfile.objects.get_or_create(user=instance)
        instance.profile.save()
