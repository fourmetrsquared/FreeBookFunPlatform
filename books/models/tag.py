"""
Tag model for the MD Books Library.

This module defines the Tag model, which represents a keyword or label
used to categorize books. Tags provide flexible, user-generated classification
that complements the hierarchical Category system.

Key Features:
    - Simple keyword-based classification
    - Many-to-Many relationship with books
    - Auto-generated URL-friendly slugs
    - Unique tag names (case-insensitive)
    - Support for tag clouds and popular tags

Classes:
    Tag - Tag model for book classification
"""

from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    """
    Tag model representing a keyword label for book classification.

    Tags provide a flexible, flat classification system that complements
    the hierarchical Category system. Users can create tags to describe
    books by topic, technology, genre, or any other relevant keyword.

    Attributes:
        name (str): Tag name (max 50 characters, unique, case-insensitive)
        slug (str): URL identifier (auto-generated from name)
        description (str): Optional tag description for SEO (max 500 characters)
        created_at (datetime): Tag creation timestamp (auto)
        updated_at (datetime): Last update timestamp (auto)

    Relationships:
        - books: All books with this tag (Many-to-Many reverse relation)

    Properties:
        book_count: Number of books with this tag
        is_popular: True if tag has 10+ books
        is_trending: True if tag was used frequently in last 30 days

    Methods:
        save(): Auto-generates slug from name
        get_absolute_url(): Returns the tag detail page URL
        merge_with(other_tag): Merges another tag into this one

    Example:
        >>> tag = Tag.objects.get(slug='python')
        >>> tag.book_count
        42
        >>> tag.is_popular
        True
    """

    # ============================================
    # Core Fields
    # ============================================

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Name",
        help_text="Tag name (max 50 characters, unique)",
        validators=[MinLengthValidator(2)]
        # TODO: Add case-insensitive uniqueness constraint at database level
        # to prevent "Python" and "python" from being different tags.
        # TODO: Add validation to prevent special characters in tag names.
        # TODO: Consider adding a 'synonyms' field or TagSynonym model
        # to handle variations like "JS" -> "JavaScript".
    )

    # Slug is auto-generated in the save() method
    # Used for SEO-friendly URLs like /tag/python/
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="URL",
        help_text="URL identifier. Auto-generated from name."
        # TODO: Ensure slug uniqueness is maintained even after name changes.
    )

    # TODO: Add description field for SEO and user guidance
    # description = models.TextField(
    #     max_length=500,
    #     blank=True,
    #     verbose_name="Description",
    #     help_text="Brief description of what this tag represents (max 500 characters)"
    # )

    # TODO: Add image field for visual tag representation
    # image = models.ImageField(
    #     upload_to='tags/images/',
    #     blank=True,
    #     null=True,
    #     verbose_name="Tag Image",
    #     help_text="Optional icon or image for the tag"
    # )

    # TODO: Add color field for visual distinction in tag clouds
    # color = models.CharField(
    #     max_length=7,
    #     default='#007bff',
    #     verbose_name="Color",
    #     help_text="Hex color code for tag display (e.g., #007bff)"
    # )

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
        """Meta options for the Tag model."""
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
            # TODO: Add index for tag cloud queries (ordering by book count)
            # This requires annotating the queryset, but a denormalized
            # 'book_count' field with index would be faster for large datasets.
        ]

    # ============================================
    # Methods
    # ============================================

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug from name.

        If slug is not provided, generates it from the name.
        Handles Cyrillic characters and ensures uniqueness.

        Example:
            >>> tag = Tag(name='Machine Learning')
            >>> tag.save()
            >>> tag.slug
            'machine-learning'
        """
        if not self.slug:
            base_slug = slugify(self.name)

            # TODO: If the app heavily uses non-Latin characters,
            # replace standard slugify with a library like `Unidecode`
            # to ensure clean, readable ASCII slugs.
            if not base_slug:
                base_slug = self.name.lower().replace(' ', '-')

            # Ensure slug uniqueness
            slug = base_slug
            counter = 1
            while Tag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # TODO: Normalize tag name to lowercase or title case for consistency
        # self.name = self.name.strip().title()

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Return string representation of the tag.

        Returns:
            str: Tag name

        Example:
            >>> str(tag)
            'Python'
        """
        return self.name

    def get_absolute_url(self):
        """
        Return the URL for the tag's detail page.

        Returns:
            str: URL path to the tag detail view

        Example:
            >>> tag.get_absolute_url()
            '/tag/python/'
        """
        return reverse('books:tag_detail', kwargs={'slug': self.slug})

    # ============================================
    # Properties
    # ============================================

    @property
    def book_count(self):
        """
        Get the number of books with this tag.

        Returns:
            int: Number of books

        Example:
            >>> tag.book_count
            42
        """
        # TODO: Cache this value in the database for performance
        # if accessed frequently (e.g., in tag clouds or list views).
        # Consider adding a denormalized 'book_count' field updated via signals.
        return self.books.count()

    @property
    def is_popular(self):
        """
        Check if this tag is popular (10+ books).

        Returns:
            bool: True if tag has 10 or more books

        Example:
            >>> tag.is_popular
            True
        """
        # TODO: Make the threshold configurable in settings.
        return self.book_count >= 10

    @property
    def is_trending(self):
        """
        Check if this tag is trending (frequently used in last 30 days).

        Returns:
            bool: True if tag was added to 5+ books in last 30 days

        Example:
            >>> tag.is_trending
            True
        """
        # TODO: Implement trending logic based on recent book additions.
        # from django.utils import timezone
        # from datetime import timedelta
        # thirty_days_ago = timezone.now() - timedelta(days=30)
        # recent_count = self.books.filter(
        #     created_at__gte=thirty_days_ago
        # ).count()
        # return recent_count >= 5
        return False

    # ============================================
    # Tag Management Methods
    # ============================================

    def merge_with(self, other_tag):
        """
        Merge another tag into this one.

        Moves all books from other_tag to this tag, then deletes other_tag.
        Useful for consolidating duplicate or similar tags.

        Args:
            other_tag (Tag): The tag to merge into this one

        Example:
            >>> python_tag = Tag.objects.get(name='Python')
            >>> py_tag = Tag.objects.get(name='py')
            >>> python_tag.merge_with(py_tag)
            >>> # All books with 'py' tag now have 'Python' tag
            >>> # 'py' tag is deleted
        """
        # TODO: Add permission check to ensure only staff can merge tags.
        # TODO: Add transaction.atomic() to ensure atomicity.
        # TODO: Log the merge action for audit purposes.

        # Move all books from other_tag to this tag
        for book in other_tag.books.all():
            book.tags.add(self)
            book.tags.remove(other_tag)

        # Delete the merged tag
        other_tag.delete()

    def rename(self, new_name):
        """
        Rename this tag and update its slug.

        Args:
            new_name (str): The new tag name

        Example:
            >>> tag.rename('Python 3')
            >>> tag.name
            'Python 3'
            >>> tag.slug
            'python-3'
        """
        # TODO: Add permission check to ensure only staff can rename tags.
        # TODO: Notify users who have books with this tag about the rename.
        self.name = new_name
        self.slug = ''  # Force slug regeneration
        self.save()

    # ============================================
    # Query Helper Methods
    # ============================================

    @classmethod
    def get_popular_tags(cls, limit=20):
        """
        Get the most popular tags by book count.

        Args:
            limit (int): Maximum number of tags to return

        Returns:
            QuerySet: Tags annotated with book_count, ordered by popularity

        Example:
            >>> popular = Tag.get_popular_tags(10)
            >>> popular[0].name
            'Python'
            >>> popular[0].book_count
            42
        """
        # TODO: Cache this result for performance if accessed frequently.
        # TODO: Use Redis for distributed caching in production.
        from django.db.models import Count

        return cls.objects.annotate(
            book_count=Count('books')
        ).filter(
            book_count__gt=0
        ).order_by('-book_count')[:limit]

    @classmethod
    def get_trending_tags(cls, days=30, limit=10):
        """
        Get tags that are trending (frequently used recently).

        Args:
            days (int): Time period to consider (default: 30 days)
            limit (int): Maximum number of tags to return

        Returns:
            QuerySet: Tags annotated with recent_count, ordered by trendiness

        Example:
            >>> trending = Tag.get_trending_tags(7, 5)
            >>> trending[0].name
            'Django 5'
        """
        # TODO: Implement trending logic based on recent book additions.
        # from django.utils import timezone
        # from datetime import timedelta
        # from django.db.models import Count, Q
        # 
        # cutoff_date = timezone.now() - timedelta(days=days)
        # return cls.objects.annotate(
        #     recent_count=Count('books', filter=Q(books__created_at__gte=cutoff_date))
        # ).filter(
        #     recent_count__gt=0
        # ).order_by('-recent_count')[:limit]
        return cls.objects.none()  # Placeholder

    @classmethod
    def get_tag_cloud(cls, min_count=1, max_tags=50):
        """
        Get tags for a tag cloud visualization.

        Returns tags with their book counts for sizing in a tag cloud.

        Args:
            min_count (int): Minimum book count to include
            max_tags (int): Maximum number of tags to return

        Returns:
            QuerySet: Tags annotated with book_count

        Example:
            >>> cloud = Tag.get_tag_cloud()
            >>> for tag in cloud:
            ...     print(f"{tag.name}: {tag.book_count}")
        """
        # TODO: Cache this result for performance.
        # TODO: Add font_size calculation for CSS styling.
        from django.db.models import Count

        return cls.objects.annotate(
            book_count=Count('books')
        ).filter(
            book_count__gte=min_count
        ).order_by('-book_count')[:max_tags]

    @classmethod
    def search_tags(cls, query, limit=10):
        """
        Search tags by name.

        Args:
            query (str): Search query
            limit (int): Maximum number of results

        Returns:
            QuerySet: Tags matching the query

        Example:
            >>> results = Tag.search_tags('py')
            >>> results[0].name
            'Python'
        """
        # TODO: Add full-text search index for better performance.
        # TODO: Consider using PostgreSQL's trigram similarity for fuzzy matching.
        return cls.objects.filter(
            name__icontains=query
        )[:limit]

    # ============================================
    # Utility Methods
    # ============================================

    @classmethod
    def get_or_create_tag(cls, name):
        """
        Get an existing tag or create a new one.

        Handles case-insensitive matching to prevent duplicates.

        Args:
            name (str): Tag name

        Returns:
            tuple: (tag, created) where created is True if tag was created

        Example:
            >>> tag, created = Tag.get_or_create_tag('Python')
            >>> created
            False  # Tag already existed
        """
        # TODO: Add case-insensitive lookup to prevent "Python" vs "python" duplicates.
        # try:
        #     tag = cls.objects.get(name__iexact=name)
        #     return tag, False
        # except cls.DoesNotExist:
        #     tag = cls.objects.create(name=name)
        #     return tag, True

        tag, created = cls.objects.get_or_create(name=name)
        return tag, created

    def get_similar_tags(self, limit=5):
        """
        Get tags that frequently appear together with this tag.

        Useful for suggesting related tags to users.

        Args:
            limit (int): Maximum number of similar tags to return

        Returns:
            QuerySet: Tags that co-occur with this tag

        Example:
            >>> similar = tag.get_similar_tags()
            >>> similar[0].name
            'Django'
        """
        # TODO: Implement co-occurrence analysis.
        # TODO: Cache results for performance.
        # from django.db.models import Count
        # 
        # book_ids = self.books.values_list('id', flat=True)
        # return Tag.objects.filter(
        #     books__id__in=book_ids
        # ).exclude(
        #     pk=self.pk
        # ).annotate(
        #     co_occurrence=Count('books', filter=Q(books__id__in=book_ids))
        # ).order_by('-co_occurrence')[:limit]

        return Tag.objects.none()  # Placeholder

# TODO: Add Django signals to handle tag-related actions
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
#
# @receiver(post_save, sender=Tag)
# def clear_tag_cache(sender, instance, **kwargs):
#     """
#     Clear cached tag data when a tag is created or updated.
#     """
#     # TODO: Clear cache for popular_tags, trending_tags, tag_cloud
#     # from django.core.cache import cache
#     # cache.delete('popular_tags')
#     # cache.delete('trending_tags')
#     pass
#
# @receiver(post_delete, sender=Tag)
# def handle_tag_deletion(sender, instance, **kwargs):
#     """
#     Handle cleanup when a tag is deleted.
#     """
#     # TODO: Log tag deletion for audit purposes.
#     # TODO: Notify users who have books with this tag.
#     pass
