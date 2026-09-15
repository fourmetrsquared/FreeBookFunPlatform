"""
Profile model for the MD Books Library.

This module defines the Profile model, which extends Django's built-in User
model with additional information like avatar, bio, social links, and
donation/payment data.

Key Features:
    - One-to-One relationship with Django's User model
    - Avatar image with default fallback
    - Social media links (GitHub, YouTube, Twitter, website)
    - Donation tracking (Stripe, PayPal)
    - Supporter status for premium features
    - Auto-generated timestamps

Classes:
    Profile - Extended user profile with social and payment information

Usage:
    from accounts.models import Profile

    # Get user's profile
    profile = request.user.profile

    # Access profile fields
    print(profile.bio)
    print(profile.github_username)

    # Check if user is a supporter
    if profile.is_supporter:
        # Show premium features
        pass

TODO: Add the following features in future iterations:
    - Profile badges system
    - Reading history tracking
    - Follower/following system
    - Notification preferences
    - Privacy settings
    - Two-factor authentication data
    - Email verification status
"""

from decimal import Decimal

from django.conf import settings
# Use get_user_model() for flexibility with custom user models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse

User = get_user_model()


class Profile(models.Model):
    """
    Extended user profile with social links, bio, and donation tracking.

    The Profile model extends Django's built-in User model with additional
    information that's not part of the core authentication system. This includes
    avatar, bio, social media links, and donation/payment data.

    Attributes:
        user (User): One-to-One link to Django's User model
        avatar (ImageField): User's profile picture
        bio (str): Short biography (max 500 characters)
        location (str): User's location (max 100 characters)
        github_username (str): GitHub username for profile link
        youtube_channel_url (str): YouTube channel URL
        twitter_url (str): Twitter/X profile URL
        website_url (str): Personal website URL
        stripe_customer_id (str): Stripe customer ID for payments
        paypal_email (str): PayPal email for donations
        total_donated (Decimal): Total amount donated by user
        is_supporter (bool): Whether user has donated at least once
        created_at (datetime): Profile creation timestamp
        updated_at (datetime): Last update timestamp

    Relationships:
        - user: Django User (One-to-One)
        - books: Books authored by this user (reverse FK from Book)
        - reviews: Reviews written by this user (reverse FK from Review)
        - category_requests: Category requests made by this user (reverse FK)
        - reviewed_categories: Categories reviewed by this user (reverse FK)

    Properties:
        has_social_links: True if user has at least one social link
        supporter_badge: HTML badge for supporters
        full_name_or_username: Full name if available, else username
        avatar_url: URL to avatar (or default)

    Methods:
        get_absolute_url(): Returns the profile page URL
        add_donation(amount): Add a donation to total
        update_supporter_status(): Recalculate is_supporter based on donations
        get_books_count(): Count of published books
        get_reviews_count(): Count of reviews

    Example:
        >>> profile = Profile.objects.get(user=user)
        >>> profile.bio
        'Python developer and tech writer'
        >>> profile.is_supporter
        True
        >>> profile.get_books_count()
        12
    """

    # ============================================
    # Core Relationship
    # ============================================

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="User",
        help_text="The Django User this profile belongs to"
    )

    # ============================================
    # Profile Information
    # ============================================

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        default='default_avatar.png',
        verbose_name="Avatar",
        help_text="Profile picture (JPG, PNG, max 2MB)"
        # TODO: Add image validation (max size, dimensions)
        # TODO: Consider using django-imagekit for automatic resizing
        # TODO: Add avatar cropping functionality
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Bio",
        help_text="Short biography about yourself (max 500 characters)"
        # TODO: Consider supporting Markdown for rich formatting
        # TODO: Add profanity filter
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Location",
        help_text="Your city or country (e.g., 'San Francisco, CA')"
    )

    # ============================================
    # Social Links
    # ============================================

    github_username = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="GitHub Username",
        help_text="Your GitHub username (e.g., 'AngelJumbo')",
        validators=[MinLengthValidator(1)]
        # TODO: Add regex validation for valid GitHub usernames
        # TODO: Auto-generate GitHub profile URL from username
    )

    youtube_channel_url = models.URLField(
        blank=True,
        max_length=255,
        verbose_name="YouTube Channel",
        help_text="Link to your YouTube channel"
        # TODO: Validate URL is actually a YouTube channel
    )

    twitter_url = models.URLField(
        blank=True,
        max_length=255,
        verbose_name="Twitter/X Profile",
        help_text="Link to your Twitter or X profile"
        # TODO: Validate URL is actually a Twitter/X profile
    )

    website_url = models.URLField(
        blank=True,
        max_length=255,
        verbose_name="Personal Website",
        help_text="Your personal website or blog URL"
    )

    # ============================================
    # Donation & Payment Fields
    # ============================================

    stripe_customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Stripe Customer ID",
        help_text="Stripe customer ID for payment processing"
        # TODO: Add validation for Stripe customer ID format (cus_...)
        # TODO: Consider encrypting this field for security
    )

    paypal_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="PayPal Email",
        help_text="PayPal email address for receiving donations"
    )

    total_donated = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Donated",
        help_text="Total amount donated by this user"
        # TODO: Add currency field (currently assumes USD)
        # TODO: Consider using a separate Donation model for transaction history
    )

    is_supporter = models.BooleanField(
        default=False,
        verbose_name="Supporter Status",
        help_text="True if user has donated at least once"
        # TODO: Consider tiered supporter levels (Bronze, Silver, Gold)
        # TODO: Add expiration date for time-limited supporter status
    )

    # ============================================
    # Timestamps
    # ============================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    # ============================================
    # Meta Options
    # ============================================

    class Meta:
        """Meta options for the Profile model."""
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_supporter']),
            # TODO: Add index for github_username if frequently queried
        ]

    # ============================================
    # String Representation & URLs
    # ============================================

    def __str__(self):
        """
        Return string representation of the profile.

        Returns:
            str: Username with "'s Profile" suffix

        Example:
            >>> str(profile)
            "john_doe's Profile"
        """
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        """
        Return the URL for the user's public profile page.

        Returns:
            str: URL path to the public profile view

        Example:
            >>> profile.get_absolute_url()
            '/accounts/profile/john_doe/'
        """
        return reverse('accounts:public_profile', kwargs={
            'username': self.user.username
        })

    # ============================================
    # Properties
    # ============================================

    @property
    def has_social_links(self):
        """
        Check if the user has at least one social link.

        Returns:
            bool: True if any social link is provided

        Example:
            >>> profile.github_username = 'AngelJumbo'
            >>> profile.has_social_links
            True
        """
        return any([
            self.github_username,
            self.youtube_channel_url,
            self.twitter_url,
            self.website_url,
        ])

    @property
    def github_profile_url(self):
        """
        Get the full GitHub profile URL from username.

        Returns:
            str|None: GitHub profile URL or None if no username

        Example:
            >>> profile.github_username = 'AngelJumbo'
            >>> profile.github_profile_url
            'https://github.com/AngelJumbo'
        """
        if self.github_username:
            return f'https://github.com/{self.github_username}'
        return None

    @property
    def supporter_badge(self):
        """
        Get HTML badge for supporters.

        Returns:
            str: HTML badge or empty string if not a supporter

        Example:
            >>> profile.is_supporter = True
            >>> profile.supporter_badge
            '<span class="badge bg-warning">⭐ Supporter</span>'
        """
        if self.is_supporter:
            return '<span class="badge bg-warning text-dark">⭐ Supporter</span>'
        return ''

    @property
    def full_name_or_username(self):
        """
        Get user's full name if available, otherwise username.

        Returns:
            str: Full name or username

        Example:
            >>> profile.user.get_full_name()
            'John Doe'
            >>> profile.full_name_or_username
            'John Doe'
        """
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username

    @property
    def avatar_url(self):
        """
        Get the URL to the user's avatar.

        Returns the avatar URL if set, otherwise returns the default avatar.

        Returns:
            str: URL to avatar image

        Example:
            >>> profile.avatar_url
            '/media/avatars/john_doe.jpg'
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return settings.MEDIA_URL + 'default_avatar.png'

    @property
    def member_since(self):
        """
        Get the date the user became a member.

        Returns:
            datetime: Profile creation date

        Example:
            >>> profile.member_since
            datetime.datetime(2024, 1, 15, 10, 30, tzinfo=...)
        """
        return self.created_at

    # ============================================
    # Donation Methods
    # ============================================

    def add_donation(self, amount):
        """
        Add a donation to the user's total.

        Args:
            amount (Decimal): Amount to add

        Example:
            >>> profile.add_donation(Decimal('25.00'))
            >>> profile.total_donated
            Decimal('25.00')
            >>> profile.is_supporter
            True
        """
        # TODO: Validate amount is positive
        # TODO: Create a Donation record for transaction history
        # TODO: Use atomic transaction for safety

        self.total_donated += amount
        self.update_supporter_status()
        self.save(update_fields=['total_donated', 'is_supporter', 'updated_at'])

    def update_supporter_status(self):
        """
        Update supporter status based on donation total.

        A user is considered a supporter if they have donated at least $1.

        Example:
            >>> profile.total_donated = Decimal('5.00')
            >>> profile.update_supporter_status()
            >>> profile.is_supporter
            True
        """
        # TODO: Make threshold configurable in settings
        self.is_supporter = self.total_donated >= Decimal('1.00')

    # ============================================
    # Content Statistics Methods
    # ============================================

    def get_books_count(self, published_only=True):
        """
        Get the number of books authored by this user.

        Args:
            published_only (bool): If True, count only published books

        Returns:
            int: Number of books

        Example:
            >>> profile.get_books_count()
            12
            >>> profile.get_books_count(published_only=False)
            15
        """
        # TODO: Cache this value for performance
        queryset = self.books.all()
        if published_only:
            queryset = queryset.filter(is_published=True)
        return queryset.count()

    def get_reviews_count(self):
        """
        Get the number of reviews written by this user.

        Returns:
            int: Number of reviews

        Example:
            >>> profile.get_reviews_count()
            42
        """
        # TODO: Cache this value for performance
        return self.reviews.count()

    def get_average_rating_given(self):
        """
        Calculate the average rating this user has given.

        Returns:
            float: Average rating (0.0 if no reviews)

        Example:
            >>> profile.get_average_rating_given()
            4.3
        """
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'))
        return result['avg'] or 0.0

    def get_total_reading_time(self):
        """
        Calculate total reading time across all authored books.

        Returns:
            int: Total reading time in minutes

        Example:
            >>> profile.get_total_reading_time()
            1250
        """
        # TODO: Cache this value for performance
        return sum(
            book.reading_time_minutes
            for book in self.books.filter(is_published=True)
        )

    # ============================================
    # Social Media Helper Methods
    # ============================================

    def get_social_links(self):
        """
        Get a dictionary of all social links.

        Returns:
            dict: Social link names and URLs

        Example:
            >>> profile.get_social_links()
            {
                'github': 'https://github.com/AngelJumbo',
                'twitter': 'https://twitter.com/...',
                'website': 'https://example.com',
            }
        """
        links = {}

        if self.github_username:
            links['github'] = self.github_profile_url

        if self.youtube_channel_url:
            links['youtube'] = self.youtube_channel_url

        if self.twitter_url:
            links['twitter'] = self.twitter_url

        if self.website_url:
            links['website'] = self.website_url

        return links

    # ============================================
    # Permission Methods
    # ============================================

    def can_edit_book(self, book):
        """
        Check if this profile's user can edit a book.

        Args:
            book (Book): The book to check

        Returns:
            bool: True if user can edit

        Example:
            >>> profile.can_edit_book(book)
            True
        """
        return book.author == self or self.user.is_staff

    def can_edit_category(self, category):
        """
        Check if this profile's user can edit a category.

        Args:
            category (Category): The category to check

        Returns:
            bool: True if user can edit
        """
        return (
                category.author == self and
                category.is_pending
        ) or self.user.is_staff

    def can_edit_review(self, review):
        """
        Check if this profile's user can edit a review.

        Args:
            review (Review): The review to check

        Returns:
            bool: True if user can edit
        """
        return review.author == self or self.user.is_staff

# ============================================
# Signals for Auto-Creating Profiles
# ============================================

# TODO: Implement signals to auto-create profiles when users are created
# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """
#     Automatically create a Profile when a User is created.
#     
#     This ensures every user has a profile without manual creation.
#     """
#     if created:
#         Profile.objects.create(user=instance)
#
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     """
#     Automatically save the Profile when the User is saved.
#     
#     This keeps the profile in sync with user changes.
#     """
#     if hasattr(instance, 'profile'):
#         instance.profile.save()


# ============================================
# Model Manager (Optional)
# ============================================

# TODO: Add custom manager for common queries
# class ProfileManager(models.Manager):
#     """Custom manager for Profile model."""
#     
#     def get_supporters(self):
#         """
#         Get all supporter profiles.
#         
#         Returns:
#             QuerySet: Profiles with is_supporter=True
#         """
#         return self.filter(is_supporter=True)
#     
#     def with_social_links(self):
#         """
#         Get profiles that have at least one social link.
#         
#         Returns:
#             QuerySet: Profiles with social links
#         """
#         return self.filter(
#             models.Q(github_username__gt='') |
#             models.Q(youtube_channel_url__gt='') |
#             models.Q(twitter_url__gt='') |
#             models.Q(website_url__gt='')
#         )
#     
#     def top_donors(self, limit=10):
#         """
#         Get top donors by total donated amount.
#         
#         Args:
#             limit (int): Maximum number of profiles to return
#         
#         Returns:
#             QuerySet: Top donor profiles
#         """
#         return self.filter(
#             is_supporter=True
#         ).order_by('-total_donated')[:limit]
