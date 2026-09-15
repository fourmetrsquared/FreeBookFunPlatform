"""
Signal handlers for the accounts application.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


# Use string reference to avoid circular imports
# Don't import Profile directly at module level!


@receiver(post_save, sender='auth.User')  # Use string reference
def create_user_profile(sender, instance, created, **kwargs):
    """Create Profile when User is created."""
    if created:
        # Import here, inside the function, to avoid circular imports
        from .models import Profile
        Profile.objects.create(user=instance)


@receiver(post_save, sender='auth.User')
def save_user_profile(sender, instance, **kwargs):
    """Save Profile when User is saved."""
    from .models import Profile
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.get_or_create(user=instance)
