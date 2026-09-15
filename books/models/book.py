"""
Book model for the MD Books Library.

This module defines the Book model, which represents a book in the library.
Books can have multiple chapters, reviews, and tags. They belong to a category
(optional) and have an author (Profile).

Classes:
    Book - Main book model with all metadata and relationships
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from accounts.models import Profile


# TODO: Import gettext_lazy for proper internationalization (i18n) if the app supports multiple languages
# from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    """
    Book model representing a published work in the library.

    Attributes:
        title (str): Book title (max 100 characters)
        slug (str): URL identifier (auto-generated from title)
        description (str): Book synopsis (max 5000 characters)
        category (Category): Book category (optional, approved only)
        author (Profile): Book author (Many-to-One relationship)
        tags (Tag): Book tags (Many-to-Many relationship)
        image (ImageField): Book cover image
        views (int): View counter (auto-incremented)
        likes (int): Like counter
        is_published (bool): Publication flag (False = draft)
        language (str): Book language
        reading_time_minutes (int): Estimated reading time in minutes
        created_at (datetime): Creation timestamp (auto)
        updated_at (datetime): Last update timestamp (auto)

    Relationships:
        - chapters: All chapters of the book (reverse relation)
        - reviews: All reviews for the book (reverse relation)

    Methods:
        save(): Auto-generates slug from title
        get_absolute_url(): Returns the detail page URL

    Example:
        >>> book = Book.objects.get(slug='learning-django')
        >>> book.chapters.count()
        12
        >>> book.average_rating
        4.5
    """

    title = models.CharField(
        max_length=100,
        verbose_name="Title",  # TODO: Wrap with _('Title') for i18n
        help_text="Enter the book title (max 100 characters)"
    )

    # Slug is auto-generated in the save() method
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="URL",
        help_text="Unique URL identifier. Auto-generated from title."
    )

    description = models.TextField(
        max_length=5000,
        verbose_name="Description",
        help_text="Brief synopsis of the book (max 5000 characters)"
    )

    # Category is optional - book can exist without a category
    # Only approved categories are available for selection
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        limit_choices_to={'status': 'approved'},
        verbose_name="Category",
        help_text="Book category (optional, approved categories only)"
        # TODO: Consider adding db_index=True if filtering by category is frequent
    )

    # Author relationship - one author can write multiple books
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='books',
        verbose_name="Author",
        help_text="The profile of the book's author"
        # TODO: Consider on_delete=models.PROTECT if you want to prevent deleting
        # authors who have published books, to preserve content integrity.
    )

    # Tags - many-to-many relationship
    # A book can have multiple tags, and a tag can belong to multiple books
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='books',
        verbose_name="Tags",
        help_text="Select relevant tags for this book"
        # TODO: Consider adding a through model if you need to store additional data
        # about the relationship (e.g., tag_order, added_by, added_at)
    )

    image = models.ImageField(
        upload_to='books/book/image/',
        blank=True,
        null=True,
        verbose_name="Cover Image",
        help_text="Upload a cover image for the book"
        # TODO: Add image validation (max size, allowed formats) or use django-imagekit
        # to automatically resize/optimize uploaded images and save storage space.
        # TODO: Consider using a CDN for image storage in production.
    )

    # View counter - atomically incremented using F() expressions
    views = models.PositiveIntegerField(
        default=0,
        verbose_name="Views",
        help_text="Automatically incremented on each view"
        # TODO: Consider moving view tracking to a separate model (BookView)
        # to track individual user views, prevent duplicate counting,
        # and enable analytics (e.g., views per day, unique visitors).
    )

    likes = models.PositiveIntegerField(
        default=0,
        verbose_name="Likes",
        help_text="Number of likes"
        # TODO: Similar to views, consider a separate Like model to track
        # which users liked the book and prevent duplicate likes.
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name="Published",
        help_text="Uncheck to save as draft"
        # TODO: Add a published_at DateTimeField to track when the book was actually published,
        # separate from created_at (which tracks when it was first created as a draft).
    )

    language = models.CharField(
        max_length=50,
        default='English',
        verbose_name="Language",
        help_text="Primary language of the book"
        # TODO: Replace with a choices field or a separate Language model
        # to standardize language options across the application.
    )

    reading_time_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Reading Time",
        help_text="Estimated reading time in minutes"
        # TODO: Auto-calculate this field based on total word count of all chapters
        # (average reading speed: 200-250 words per minute).
        # TODO: Update this field automatically when chapters are added/edited/deleted.
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        """Meta options for the Book model."""
        ordering = ['-created_at']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_published']),
            # TODO: Add composite index for (is_published, -created_at)
            # if the main book list frequently queries "WHERE is_published=True ORDER BY -created_at"
            # TODO: Add index on author field if filtering by author is common
            # TODO: Add full-text search index on title and description for better search performance
        ]

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug from title.

        If slug is not provided, generates it from the title.
        Handles Cyrillic characters and ensures uniqueness.

        Example:
            >>> book = Book(title='Learning Django')
            >>> book.save()
            >>> book.slug
            'learning-django'
        """
        if not self.slug:
            base_slug = slugify(self.title)

            # TODO: If the app heavily uses non-Latin characters (e.g., Cyrillic, Arabic),
            # replace standard slugify with a library like `Unidecode` or `django-autoslug`
            # to ensure clean, readable ASCII slugs (e.g., "программирование" -> "programmirovanie").
            if not base_slug:
                base_slug = self.title.lower().replace(' ', '-')

            # Ensure slug uniqueness
            slug = base_slug
            counter = 1
            while Book.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # TODO: Add validation to prevent publishing a book without at least one chapter
        # if self.is_published and not self.chapters.exists():
        #     raise ValidationError("Cannot publish a book without chapters")

        # TODO: Auto-calculate reading_time_minutes before saving
        # if not self.reading_time_minutes:
        #     self.reading_time_minutes = self.calculate_reading_time()

        super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation of the book."""
        return self.title

    def get_absolute_url(self):
        """
        Return the URL for the book's detail page.

        Returns:
            str: URL path to the book detail view

        Example:
            >>> book.get_absolute_url()
            '/book/learning-django/'
        """
        return reverse('books:book_detail', kwargs={'slug': self.slug})

    @property
    def average_rating(self):
        """
        Calculate the average rating from all reviews.

        Returns:
            float: Average rating (0.0 if no reviews)

        Example:
            >>> book.average_rating
            4.5
        """
        # TODO: This property executes a database query every time it's accessed.
        # If used in a list view (e.g., displaying 20 books), this causes 20 additional queries.
        # Solution: Use annotate(avg_rating=Avg('reviews__rating')) in the View's queryset
        # and access book.avg_rating instead of book.average_rating.
        result = self.reviews.aggregate(models.Avg('rating'))
        return result['rating__avg'] or 0.0

    @property
    def review_count(self):
        """
        Return the total number of reviews.

        Returns:
            int: Number of reviews
        """
        # TODO: Same N+1 query problem as average_rating.
        # Use annotate(review_count=Count('reviews')) in the View's queryset.
        return self.reviews.count()

    @property
    def chapter_count(self):
        """
        Return the total number of published chapters.

        Returns:
            int: Number of published chapters
        """
        # TODO: Same N+1 query problem.
        # Use annotate(chapter_count=Count('chapters', filter=Q(chapters__is_published=True)))
        # in the View's queryset.
        return self.chapters.filter(is_published=True).count()

    # TODO: Add a method to calculate reading time based on word count
    # def calculate_reading_time(self):
    #     """
    #     Calculate estimated reading time based on total word count.
    #     Average reading speed: 200-250 words per minute.
    #
    #     Returns:
    #         int: Estimated reading time in minutes
    #     """
    #     total_words = sum(
    #         len(chapter.content.split())
    #         for chapter in self.chapters.filter(is_published=True)
    #     )
    #     return max(1, total_words // 225)  # 225 words per minute average

    # TODO: Add a method to get total word count
    # def get_word_count(self):
    #     """
    #     Get total word count across all published chapters.
    #
    #     Returns:
    #         int: Total word count
    #     """
    #     return sum(
    #         len(chapter.content.split())
    #         for chapter in self.chapters.filter(is_published=True)
    #     )

    # TODO: Add a method to check if current user can edit this book
    # def can_edit(self, user):
    #     """
    #     Check if the given user can edit this book.
    #
    #     Args:
    #         user (User): The user to check permissions for
    #
    #     Returns:
    #         bool: True if user can edit, False otherwise
    #     """
    #     return (
    #         user.is_authenticated and
    #         (self.author.user == user or user.is_staff)
    #     )

    # TODO: Add a method to increment views atomically
    # def increment_views(self):
    #     """
    #     Atomically increment the view counter.
    #     Uses F() expression to prevent race conditions.
    #     """
    #     Book.objects.filter(pk=self.pk).update(views=models.F('views') + 1)
    #     self.views += 1

    # TODO: Add a method to increment likes atomically
    # def increment_likes(self):
    #     """
    #     Atomically increment the like counter.
    #     Uses F() expression to prevent race conditions.
    #     """
    #     Book.objects.filter(pk=self.pk).update(likes=models.F('likes') + 1)
    #     self.likes += 1

    # TODO: Add a method to decrement likes atomically
    # def decrement_likes(self):
    #     """
    #     Atomically decrement the like counter.
    #     Uses F() expression to prevent race conditions.
    #     Ensures likes don't go below 0.
    #     """
    #     Book.objects.filter(pk=self.pk).update(likes=models.F('likes') - 1)
    #     self.likes = max(0, self.likes - 1)
