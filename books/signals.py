"""
Signal handlers for the books application.

Signals are automatically connected when the app is loaded
via the ready() method in apps.py.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Book, Review, Chapter


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_book_rating_cache(sender, instance, **kwargs):
    """
    Update book's cached average rating when a review is saved or deleted.

    This avoids recalculating the average on every page load.
    """
    book = instance.book

    # Calculate new average
    result = book.reviews.aggregate(avg=Avg('rating'))
    avg_rating = result['avg'] or 0.0

    # TODO: Update cached field on Book model
    # book.cached_average_rating = avg_rating
    # book.cached_review_count = book.reviews.count()
    # book.save(update_fields=['cached_average_rating', 'cached_review_count'])

    # TODO: Invalidate cache
    # from django.core.cache import cache
    # cache.delete(f'book_{book.id}_rating')


@receiver(post_save, sender=Chapter)
@receiver(post_delete, sender=Chapter)
def update_book_reading_time(sender, instance, **kwargs):
    """
    Update book's reading time when chapters change.

    Recalculates total word count and estimated reading time.
    """
    book = instance.book

    # Calculate total word count
    total_words = sum(
        len(chapter.content.split())
        for chapter in book.chapters.filter(is_published=True)
    )

    # Update reading time (225 words per minute average)
    reading_time = max(1, total_words // 225)

    # TODO: Update cached field on Book model
    # book.reading_time_minutes = reading_time
    # book.save(update_fields=['reading_time_minutes'])


@receiver(pre_save, sender=Book)
def validate_book_before_save(sender, instance, **kwargs):
    """
    Validate book before saving.

    Ensures published books have at least one chapter.
    """
    if instance.is_published and instance.pk:
        # Check if book has chapters
        if not instance.chapters.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError(
                'Cannot publish a book without at least one chapter.'
            )

# TODO: Add more signals as needed
# - Category approval notifications
# - Tag usage tracking
# - Review moderation alerts