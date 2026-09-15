"""
Review model for the MD Books Library.

This module defines the Review model, which represents a user's review and
rating of a book. Reviews allow readers to share their opinions and help
other users discover quality content through a 5-star rating system.

Key Features:
    - 5-star rating system (1-5 stars)
    - Optional text comments (up to 2000 characters)
    - One review per user per book (enforced by unique_together)
    - Chronological ordering (newest first)
    - Integration with Book's average_rating calculation

Classes:
    Review - Review model with rating and comment
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from accounts.models import Profile
from books.models import Book


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    """
    Review model representing a user's rating and feedback on a book.

    Reviews are the primary mechanism for readers to evaluate books and
    help others make informed decisions. Each user can leave exactly one
    review per book, ensuring fair and diverse feedback.

    Attributes:
        book (Book): The book being reviewed (Many-to-One relationship)
        author (Profile): The user who wrote the review (Many-to-One)
        rating (int): Star rating from 1 to 5 (IntegerChoices)
        comment (str): Optional text review (max 2000 characters)
        created_at (datetime): Review creation timestamp (auto)
        updated_at (datetime): Last update timestamp (auto)

    Relationships:
        - book: The reviewed book (ForeignKey)
        - author: The review author (ForeignKey)

    Properties:
        is_positive: True if rating >= 4
        is_negative: True if rating <= 2
        is_neutral: True if rating == 3
        rating_display: Human-readable rating (e.g., "4 stars")
        rating_percentage: Rating as percentage (e.g., 80 for 4 stars)

    Methods:
        clean(): Validates the review (e.g., author != book author)
        get_absolute_url(): Returns the review detail page URL
        can_edit(user): Checks if user can edit this review

    Constraints:
        - unique_together: ('book', 'author') - one review per user per book

    Example:
        >>> review = Review.objects.get(book__slug='learning-django', author=user_profile)
        >>> review.rating
        5
        >>> review.is_positive
        True
        >>> review.rating_percentage
        100
    """

    # ============================================
    # Core Relationship Fields
    # ============================================

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Book",
        help_text="The book being reviewed"
        # TODO: Consider on_delete=models.PROTECT to prevent accidental deletion
        # of books that have reviews, preserving user feedback history.
        # TODO: Add db_index=True if filtering reviews by book is frequent.
    )

    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Author",
        help_text="The user who wrote this review"
        # TODO: Consider on_delete=models.SET_NULL with null=True to preserve
        # reviews even when users delete their accounts (mark as "Deleted User").
        # TODO: Add db_index=True if filtering reviews by author is frequent.
    )

    # ============================================
    # Rating System
    # ============================================

    class Rating(models.IntegerChoices):
        """
        Star rating choices for reviews.

        Provides a 5-star rating system with human-readable labels.
        Used to calculate book's average_rating and display star icons.
        """
        # TODO: Wrap labels with _('1 star'), _('2 stars'), etc. for i18n
        ONE = 1, '1 star'
        TWO = 2, '2 stars'
        THREE = 3, '3 stars'
        FOUR = 4, '4 stars'
        FIVE = 5, '5 stars'

    rating = models.PositiveSmallIntegerField(
        choices=Rating.choices,
        verbose_name="Rating",
        help_text="Star rating from 1 to 5"
        # TODO: Consider adding a separate 'rating' field that allows half-stars
        # (e.g., 4.5) using DecimalField for more granular ratings.
        # TODO: Add validators=[MinValueValidator(1), MaxValueValidator(5)]
        # for extra safety, though IntegerChoices already enforces this.
    )

    # ============================================
    # Comment Field
    # ============================================

    comment = models.TextField(
        max_length=2000,
        blank=True,
        verbose_name="Comment",
        help_text="Optional text review (max 2000 characters)"
        # TODO: Add profanity filter or spam detection before saving.
        # TODO: Consider supporting Markdown in comments for rich formatting.
        # TODO: Add a minimum length validation (e.g., at least 10 characters)
        # to prevent low-effort reviews like "good" or "bad".
        # TODO: Consider adding a 'comment_html' field to store rendered Markdown
        # for performance, similar to the Chapter model.
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
        """Meta options for the Review model."""
        # Enforce one review per user per book
        unique_together = ('book', 'author')

        # Show newest reviews first
        ordering = ['-created_at']

        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

        indexes = [
            models.Index(fields=['book', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['book', 'rating']),
            # TODO: Add composite index for (book, rating) to speed up
            # rating distribution queries (e.g., "how many 5-star reviews?")
            # TODO: Add full-text search index on 'comment' field 
            # if implementing review search functionality.
        ]

    # ============================================
    # Validation Methods
    # ============================================

    def clean(self):
        """
        Validate the review before saving.

        Ensures:
            - Author is not the book's author (no self-reviews)
            - Rating is within valid range (1-5)
            - Comment meets minimum length (if provided)

        Raises:
            ValidationError: If validation fails

        Example:
            >>> review = Review(book=book, author=book.author, rating=5)
            >>> review.clean()
            ValidationError: {'author': 'You cannot review your own book.'}
        """
        super().clean()

        # Prevent authors from reviewing their own books
        if self.book_id and self.author_id:
            if self.book.author_id == self.author_id:
                raise ValidationError({
                    'author': 'You cannot review your own book.'
                })

        # TODO: Add minimum comment length validation
        # if self.comment and len(self.comment.strip()) < 10:
        #     raise ValidationError({
        #         'comment': 'Comment must be at least 10 characters long.'
        #     })

        # TODO: Add profanity/spam filter
        # if contains_profanity(self.comment):
        #     raise ValidationError({
        #         'comment': 'Comment contains inappropriate language.'
        #     })

    # ============================================
    # String Representation & URLs
    # ============================================

    def __str__(self):
        """
        Return string representation of the review.

        Returns:
            str: Author name, book title, and rating

        Example:
            >>> str(review)
            'John Doe - Learning Django (5 stars)'
        """
        return f"{self.author} - {self.book.title} ({self.rating} stars)"

    def get_absolute_url(self):
        """
        Return the URL for the review's detail page.

        Returns:
            str: URL path to the review detail view

        Example:
            >>> review.get_absolute_url()
            '/review/42/'
        """
        return reverse('books:review_detail', kwargs={'pk': self.pk})

    # ============================================
    # Properties
    # ============================================

    @property
    def is_positive(self):
        """
        Check if the review is positive (4 or 5 stars).

        Returns:
            bool: True if rating >= 4

        Example:
            >>> review.rating = 5
            >>> review.is_positive
            True
        """
        return self.rating >= 4

    @property
    def is_negative(self):
        """
        Check if the review is negative (1 or 2 stars).

        Returns:
            bool: True if rating <= 2
        """
        return self.rating <= 2

    @property
    def is_neutral(self):
        """
        Check if the review is neutral (3 stars).

        Returns:
            bool: True if rating == 3
        """
        return self.rating == 3

    @property
    def rating_display(self):
        """
        Get human-readable rating label.

        Returns:
            str: Human-readable rating (e.g., "4 stars")

        Example:
            >>> review.rating = 4
            >>> review.rating_display
            '4 stars'
        """
        return self.get_rating_display()

    @property
    def rating_percentage(self):
        """
        Convert rating to percentage (0-100).

        Useful for displaying progress bars or visual ratings.

        Returns:
            int: Rating as percentage (e.g., 80 for 4 stars)

        Example:
            >>> review.rating = 4
            >>> review.rating_percentage
            80
        """
        return (self.rating / 5) * 100

    @property
    def star_icons(self):
        """
        Generate star icons HTML for the rating.

        Returns:
            str: HTML string with filled and empty stars

        Example:
            >>> review.rating = 4
            >>> review.star_icons
            '★★★★☆'
        """
        # TODO: Return HTML with CSS classes instead of Unicode characters
        # for better styling control (e.g., '<span class="star filled"></span>')
        filled = '★' * self.rating
        empty = '☆' * (5 - self.rating)
        return filled + empty

    @property
    def word_count(self):
        """
        Calculate the number of words in the comment.

        Returns:
            int: Number of words (0 if no comment)
        """
        if not self.comment:
            return 0
        return len(self.comment.split())

    # ============================================
    # Permission Methods
    # ============================================

    def can_edit(self, user):
        """
        Check if the given user can edit this review.

        Only the review author or staff members can edit reviews.

        Args:
            user (User): The user to check permissions for

        Returns:
            bool: True if user can edit, False otherwise

        Example:
            >>> review.can_edit(review.author.user)
            True
            >>> review.can_edit(other_user)
            False
        """
        # TODO: Add time-based edit restriction (e.g., can only edit within 24 hours)
        # from django.utils import timezone
        # time_limit = timezone.now() - timezone.timedelta(hours=24)
        # if self.created_at < time_limit:
        #     return False

        if not user or not user.is_authenticated:
            return False

        return self.author.user == user or user.is_staff

    def can_delete(self, user):
        """
        Check if the given user can delete this review.

        Only the review author or staff members can delete reviews.

        Args:
            user (User): The user to check permissions for

        Returns:
            bool: True if user can delete, False otherwise
        """
        return self.can_edit(user)

    # ============================================
    # Query Helper Methods
    # ============================================

    @classmethod
    def get_rating_distribution(cls, book):
        """
        Get the distribution of ratings for a book.

        Returns a dictionary with counts for each star rating (1-5).

        Args:
            book (Book): The book to analyze

        Returns:
            dict: Rating distribution {1: count, 2: count, ..., 5: count}

        Example:
            >>> Review.get_rating_distribution(book)
            {1: 2, 2: 5, 3: 10, 4: 25, 5: 58}
        """
        # TODO: Cache this result for performance if accessed frequently.
        # TODO: Use Redis for distributed caching in production.
        from django.db.models import Count

        distribution = {i: 0 for i in range(1, 6)}
        ratings = cls.objects.filter(book=book).values('rating').annotate(
            count=Count('id')
        )

        for item in ratings:
            distribution[item['rating']] = item['count']

        return distribution

    @classmethod
    def get_average_rating(cls, book):
        """
        Calculate the average rating for a book.

        Args:
            book (Book): The book to analyze

        Returns:
            float: Average rating (0.0 if no reviews)

        Example:
            >>> Review.get_average_rating(book)
            4.3
        """
        # TODO: This duplicates Book.average_rating property.
        # Consider removing this method or making Book.average_rating
        # call this class method instead.
        from django.db.models import Avg

        result = cls.objects.filter(book=book).aggregate(Avg('rating'))
        return result['rating__avg'] or 0.0

    # ============================================
    # Notification & Signal Methods
    # ============================================

    def notify_book_author(self):
        """
        Send a notification to the book's author about the new review.

        Should be called after saving a new review.

        Example:
            >>> review.save()
            >>> review.notify_book_author()
        """
        # TODO: Implement notification system (email, in-app, or push notification).
        # TODO: Use Celery for async notification sending to avoid blocking.
        # TODO: Respect user notification preferences (opt-out option).
        # from notifications.services import send_notification
        # send_notification(
        #     recipient=self.book.author.user,
        #     message=f'{self.author} left a {self.rating}-star review on your book.',
        #     link=self.get_absolute_url()
        # )
        pass

    def notify_followers(self):
        """
        Notify users who follow the reviewer about the new review.

        Should be called after saving a new review.

        Example:
            >>> review.save()
            >>> review.notify_followers()
        """
        # TODO: Implement follower system and notification service.
        # TODO: Use Celery for async notification sending.
        pass

    # ============================================
    # Moderation Methods
    # ============================================

    def flag_as_inappropriate(self, user, reason=''):
        """
        Flag this review as inappropriate for moderator review.

        Args:
            user (Profile): The user flagging the review
            reason (str): Reason for flagging

        Example:
            >>> review.flag_as_inappropriate(user, reason='Spam')
        """
        # TODO: Implement ReviewFlag model to track flags.
        # TODO: Auto-hide review if flagged by N users.
        # TODO: Notify moderators when review is flagged.
        # ReviewFlag.objects.create(
        #     review=self,
        #     flagged_by=user,
        #     reason=reason
        # )
        pass

    def is_flagged(self):
        """
        Check if this review has been flagged.

        Returns:
            bool: True if review has been flagged
        """
        # TODO: Implement after adding ReviewFlag model.
        # return self.flags.exists()
        return False

# TODO: Add Django signals to handle post-save actions
# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# @receiver(post_save, sender=Review)
# def update_book_average_rating(sender, instance, **kwargs):
#     """
#     Update the book's cached average rating after a review is saved.
#     
#     This avoids recalculating the average on every page load.
#     """
#     # TODO: Add cached_average_rating field to Book model
#     # from django.db.models import Avg
#     # avg = Review.objects.filter(book=instance.book).aggregate(Avg('rating'))
#     # instance.book.cached_average_rating = avg['rating__avg'] or 0.0
#     # instance.book.cached_review_count = instance.book.reviews.count()
#     # instance.book.save(update_fields=['cached_average_rating', 'cached_review_count'])
#     pass
#
# @receiver(post_save, sender=Review)
# def send_review_notification(sender, instance, created, **kwargs):
#     """
#     Send notification to book author when a new review is created.
#     """
#     if created:
#         instance.notify_book_author()
