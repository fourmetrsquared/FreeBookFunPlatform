"""
Category model for the MD Books Library.

This module defines the Category model, which represents a book classification
with a request-approval workflow. Users can propose new categories, and 
moderators approve or reject them to ensure quality control.

Workflow:
    1. User creates a category request (status: PENDING)
    2. Moderator reviews the request
    3. Moderator approves (status: APPROVED) or rejects (status: REJECTED)
    4. Only APPROVED categories can be assigned to books
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from accounts.models import Profile


# TODO: Import gettext_lazy for proper internationalization (i18n) if the app supports multiple languages
# from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Category model representing a book classification with request-approval workflow.
    """

    # ============================================
    # Basic Fields
    # ============================================

    title = models.CharField(
        max_length=100,
        verbose_name="Title",  # TODO: Wrap with _('Title') for i18n
        help_text="Category name (max 100 characters)"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="URL",
        help_text="Unique URL identifier. Auto-generated from title."
    )

    description = models.TextField(
        max_length=10000,
        blank=True,
        verbose_name="Description",
        help_text="Detailed description of the category (max 10000 characters)"
    )

    image = models.ImageField(
        upload_to='books/category/',
        blank=True,
        null=True,
        verbose_name="Cover Image",
        help_text="Upload a cover image for the category (optional)"
        # TODO: Add image validation (max size, allowed formats) or use django-imagekit 
        # to automatically resize/optimize uploaded images and save storage space.
    )

    # ============================================
    # Author & Moderation Fields
    # ============================================

    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='category_requests',
        verbose_name="Request Author",
        help_text="User who proposed this category"
        # TODO: Consider on_delete=models.PROTECT if you want to prevent deleting 
        # users who have pending/approved category requests, to preserve audit trails.
    )

    class Status(models.TextChoices):
        """Category approval status choices."""
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
        help_text="Current approval status of the category request"
    )

    reviewed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_categories',
        verbose_name="Reviewed By",
        help_text="Moderator who reviewed this request"
    )

    rejection_reason = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name="Rejection Reason",
        help_text="Reason for rejecting this category (if rejected)"
    )

    # ============================================
    # Timestamp Fields
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
        ordering = ['-created_at']
        verbose_name = 'Category Request'
        verbose_name_plural = 'Category Requests'

        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            # TODO: Add a composite index for (status, created_at) if the moderator 
            # dashboard frequently queries "ORDER BY created_at WHERE status = 'pending'"
        ]

    # ============================================
    # Methods
    # ============================================

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug from title.
        """
        if not self.slug:
            base_slug = slugify(self.title)

            # TODO: If the app heavily uses non-Latin characters (e.g., Cyrillic, Arabic),
            # replace standard slugify with a library like `Unidecode` or `django-autoslug`
            # to ensure clean, readable ASCII slugs (e.g., "программирование" -> "programmirovanie").
            if not base_slug:
                base_slug = self.title.lower().replace(' ', '-')

            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse('books:category_detail', kwargs={'slug': self.slug})

    # ============================================
    # Properties
    # ============================================

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def is_rejected(self):
        return self.status == self.Status.REJECTED

    # ============================================
    # Action Methods
    # ============================================

    def approve(self, reviewer):
        """
        Approve this category request.
        """
        # TODO: Add a permission check here or in the calling view to ensure 
        # the 'reviewer' actually has 'books.moderate_category' permissions.
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.rejection_reason = ''
        self.save()

        # TODO: Trigger a notification (email, in-app notification, or WebSocket) 
        # to inform the 'self.author' that their category request was approved.

    def reject(self, reviewer, reason=''):
        """
        Reject this category request.
        """
        # TODO: Add a permission check here to ensure the 'reviewer' is a moderator.
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.rejection_reason = reason
        self.save()

        # TODO: Trigger a notification to inform the 'self.author' about the rejection 
        # and provide the 'reason' so they can improve their next request.

    # ============================================
    # Query Methods
    # ============================================

    def get_books_count(self):
        """Return the number of books in this category."""
        # TODO: If this is called frequently in a list view, consider adding 
        # an annotated count in the View's queryset instead of calling this per instance 
        # to avoid the N+1 query problem.
        return self.books.count()

    @classmethod
    def get_approved_categories(cls):
        """Class method to get all approved categories."""
        # TODO: Add .cache() or Redis caching here if this queryset is accessed 
        # on every page load (e.g., for a global navigation menu).
        return cls.objects.filter(status=cls.Status.APPROVED)

    @classmethod
    def get_pending_categories(cls):
        """Class method to get all pending category requests."""
        return cls.objects.filter(status=cls.Status.PENDING)
