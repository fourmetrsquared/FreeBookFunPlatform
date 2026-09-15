from django.contrib.auth import get_user_model
from django.db import models
from decimal import Decimal

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, default='default_avatar.png')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    github_username = models.CharField(max_length=50, blank=True, help_text="e.g., AngelJumbo")
    youtube_channel_url = models.URLField(blank=True, max_length=255)
    twitter_url = models.URLField(blank=True, max_length=255)
    website_url = models.URLField(blank=True, max_length=255)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    total_donated = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_supporter = models.BooleanField(default=False, help_text="True if they have donated at least once")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

