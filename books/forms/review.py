"""
Review form for the MD Books Library.

This module defines the ModelForm for creating and editing book reviews.
Reviews allow readers to rate books (1-5 stars) and share their feedback
through optional text comments.

Key Features:
    - Bootstrap-styled form controls
    - Interactive star rating widget
    - Auto-exclusion of system-managed fields
    - Custom validation for review data
    - Self-review prevention (author cannot review own book)
    - Duplicate review prevention (one review per user per book)
    - Minimum comment length validation
    - Profanity/spam filter placeholder

Classes:
    ReviewForm - ModelForm for Review model
    StarRatingWidget - Custom widget for star rating input
"""

from django import forms
from django.core.exceptions import ValidationError

from books.models import Review


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


# ============================================
# Custom Widgets
# ============================================

class StarRatingWidget(forms.RadioSelect):
    """
    Custom widget for star rating input.

    Renders rating choices as clickable star icons instead of
    a standard dropdown select. Provides better UX for rating input.

    Features:
        - Visual star icons (★/☆) instead of numbers
        - Hover effects for better feedback
        - Accessible with proper ARIA labels
        - Works with JavaScript for interactive highlighting

    Example:
        >>> widget = StarRatingWidget()
        >>> widget.render('rating', 4)
        '<div class="star-rating">...</div>'
    """

    template_name = 'books/widgets/star_rating.html'

    # TODO: Create the template file with proper star rendering
    # Or use option_template_name for individual star rendering

    def __init__(self, attrs=None):
        """Initialize the widget with default star-rating classes."""
        default_attrs = {
            'class': 'star-rating-input',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def get_context(self, name, value, attrs):
        """
        Add star-specific context to the widget.

        Adds CSS classes and data attributes for JavaScript
        interaction (hover effects, selection highlighting).
        """
        context = super().get_context(name, value, attrs)

        # TODO: Add star-specific attributes
        # context['widget']['attrs']['data-star-count'] = '5'
        # context['widget']['attrs']['data-current-rating'] = value or '0'

        return context


class StarRatingSelect(forms.Select):
    """
    Alternative star rating widget using a select dropdown.

    Renders as a styled select element with star labels.
    Simpler than RadioSelect but less interactive.

    TODO: Consider using this as fallback for mobile devices
    where hover effects don't work well.
    """

    def __init__(self, attrs=None, choices=()):
        """Initialize with star-rating styling."""
        default_attrs = {
            'class': 'form-control star-rating-select',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, choices=choices)


# ============================================
# Main Form Class
# ============================================

class ReviewForm(forms.ModelForm):
    """
    ModelForm for creating and editing book reviews.

    This form handles the user-facing interface for review submission.
    It automatically excludes system-managed fields (book, author, timestamps)
    and provides Bootstrap-styled widgets with interactive star rating.

    Excluded Fields:
        - book: Set automatically from URL parameter in the view
        - author: Set automatically from request.user.profile
        - created_at: Auto-set on creation
        - updated_at: Auto-updated on save

    Customizations:
        - Bootstrap form-control classes on all widgets
        - Custom StarRatingWidget for interactive star input
        - Placeholder text for better UX
        - Textarea with appropriate row counts

    Validation:
        - Rating must be between 1 and 5
        - Comment minimum length (if provided)
        - Self-review prevention (author != book author)
        - Duplicate review prevention (one per user per book)
        - Profanity/spam filter

    Example:
        >>> form = ReviewForm(data=request.POST, book=book, user=request.user)
        >>> if form.is_valid():
        ...     review = form.save(commit=False)
        ...     review.book = book
        ...     review.author = request.user.profile
        ...     review.save()
    """

    class Meta:
        """Meta configuration for the ReviewForm."""
        model = Review

        # Fields to exclude from the form
        # These are managed automatically by the system
        exclude = [
            'book',  # Set from URL parameter in view
            'author',  # Set from request.user.profile
            'created_at',  # Auto-set on creation
            'updated_at',  # Auto-updated on save
        ]

        # TODO: Consider using 'fields' instead of 'exclude' for explicit control
        # fields = ['rating', 'comment']

        # Widget customizations for Bootstrap styling and star rating
        widgets = {
            'rating': StarRatingWidget(attrs={
                'class': 'star-rating-input',
                # TODO: Add data attributes for JavaScript interaction
                # 'data-star-count': '5',
                # 'data-hover-effect': 'true',
                # 'data-required': 'true',
            }),

            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your thoughts about this book (optional, max 2000 characters)',
                'maxlength': '2000',
                # TODO: Add character counter with JavaScript
                # 'data-counter': 'true',
                # TODO: Add Markdown support indicator
                # 'data-markdown-supported': 'true',
            }),
        }

        # TODO: Add help texts for form fields
        # help_texts = {
        #     'rating': 'Rate this book from 1 to 5 stars.',
        #     'comment': 'Share your detailed thoughts about the book. '
        #                'What did you like or dislike? Who would you recommend it to?',
        # }

        # TODO: Add custom labels if needed
        # labels = {
        #     'rating': 'Your Rating',
        #     'comment': 'Your Review (optional)',
        # }

        # TODO: Add error messages for better UX
        # error_messages = {
        #     'rating': {
        #         'required': 'Please select a rating.',
        #         'invalid_choice': 'Invalid rating. Please choose 1-5 stars.',
        #     },
        #     'comment': {
        #         'max_length': 'Review is too long. Maximum 2000 characters allowed.',
        #     },
        # }

    # ============================================
    # Custom Field Definitions
    # ============================================

    # TODO: Add optional fields for enhanced reviews
    # review_title = forms.CharField(
    #     max_length=100,
    #     required=False,
    #     widget=forms.TextInput(attrs={
    #         'class': 'form-control',
    #         'placeholder': 'Review title (optional)',
    #     }),
    #     help_text='Give your review a catchy title'
    # )

    # would_recommend = forms.BooleanField(
    #     required=False,
    #     widget=forms.CheckboxInput(attrs={
    #         'class': 'form-check-input',
    #     }),
    #     help_text='Would you recommend this book to others?'
    # )

    # reading_status = forms.ChoiceField(
    #     choices=[
    #         ('completed', 'Completed'),
    #         ('in_progress', 'In Progress'),
    #         ('abandoned', 'Abandoned'),
    #     ],
    #     required=False,
    #     widget=forms.RadioSelect(attrs={
    #         'class': 'form-check-input',
    #     }),
    #     help_text='Your reading status for this book'
    # )

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing additional context like the book instance
        and current user for custom validation.

        Custom kwargs:
            book (Book): The book being reviewed
            user (User): The currently authenticated user
        """
        # Extract custom kwargs before calling super()
        self.book = kwargs.pop('book', None)
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # TODO: Set rating choices with star labels
        # self.fields['rating'].choices = [
        #     (1, '★☆☆☆☆ - Poor'),
        #     (2, '★★☆☆☆ - Fair'),
        #     (3, '★★★☆☆ - Good'),
        #     (4, '★★★★☆ - Very Good'),
        #     (5, '★★★★★ - Excellent'),
        # ]

        # TODO: Make comment required for low ratings (1-2 stars)
        # to encourage constructive feedback
        # if self.data.get('rating') and int(self.data.get('rating')) <= 2:
        #     self.fields['comment'].required = True
        #     self.fields['comment'].help_text = (
        #         'Please explain your low rating to help the author improve.'
        #     )

        # TODO: Add Markdown toolbar for comment field
        # self.fields['comment'].widget.attrs['data-markdown-toolbar'] = 'true'

        # TODO: Check if user already reviewed this book
        # if self.book and self.user:
        #     existing_review = Review.objects.filter(
        #         book=self.book,
        #         author=self.user.profile
        #     ).first()
        #     if existing_review:
        #         # Pre-fill form with existing review data
        #         self.initial['rating'] = existing_review.rating
        #         self.initial['comment'] = existing_review.comment

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_rating(self):
        """
        Validate the star rating.

        Ensures:
            - Rating is provided
            - Rating is between 1 and 5
            - Rating is a valid integer

        Returns:
            int: Cleaned rating value

        Raises:
            ValidationError: If validation fails
        """
        rating = self.cleaned_data.get('rating')

        if rating is None:
            raise ValidationError('Please select a rating.')

        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationError('Rating must be between 1 and 5 stars.')

        return rating

    def clean_comment(self):
        """
        Validate the review comment.

        Ensures:
            - Comment is not just whitespace (if provided)
            - Comment meets minimum length (if provided)
            - Comment doesn't contain profanity/spam

        Returns:
            str: Cleaned comment

        Raises:
            ValidationError: If validation fails
        """
        comment = self.cleaned_data.get('comment', '').strip()

        # Comment is optional, but if provided, should be meaningful
        if not comment:
            return comment

        # TODO: Make minimum length configurable in settings
        min_length = 10
        if len(comment) < min_length:
            raise ValidationError(
                f'Comment must be at least {min_length} characters long. '
                'Please provide more detailed feedback.'
            )

        # TODO: Add profanity/spam filter
        # if contains_profanity(comment):
        #     raise ValidationError(
        #         'Your review contains inappropriate language. '
        #         'Please revise your comment.'
        #     )

        # TODO: Check for low-effort reviews (e.g., repeated characters)
        # if len(set(comment)) < 5 and len(comment) > 20:
        #     raise ValidationError(
        #         'Please provide a meaningful review.'
        #     )

        # TODO: Check for links (prevent spam)
        # import re
        # if re.search(r'https?://', comment):
        #     raise ValidationError(
        #         'Links are not allowed in reviews to prevent spam.'
        #     )

        return comment

    # ============================================
    # Form-Level Validation
    # ============================================

    def clean(self):
        """
        Perform form-level validation.

        Validates relationships between fields and prevents:
            - Self-reviews (author cannot review own book)
            - Duplicate reviews (one per user per book)

        Returns:
            dict: Cleaned data

        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()

        # Prevent authors from reviewing their own books
        if self.book and self.user:
            from accounts.models import Profile

            # Get user's profile (handle case where profile might not exist)
            try:
                user_profile = self.user.profile
            except Profile.DoesNotExist:
                raise ValidationError(
                    'You must complete your profile before leaving reviews.'
                )

            # Check if user is the book's author
            if self.book.author_id == user_profile.id:
                raise ValidationError(
                    'You cannot review your own book. '
                    'Please let others share their feedback!'
                )

            # Check for duplicate reviews (one per user per book)
            existing_review = Review.objects.filter(
                book=self.book,
                author=user_profile
            )

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                existing_review = existing_review.exclude(pk=self.instance.pk)

            if existing_review.exists():
                raise ValidationError(
                    'You have already reviewed this book. '
                    'You can edit your existing review instead.'
                )

        # TODO: Add cross-field validation
        # Example: If rating is low (1-2), require a comment
        # rating = cleaned_data.get('rating')
        # comment = cleaned_data.get('comment', '').strip()
        # if rating and rating <= 2 and not comment:
        #     self.add_error(
        #         'comment',
        #         'Please explain your low rating to help the author improve.'
        #     )

        # TODO: Validate comment vs. rating consistency
        # Very positive words with low rating (or vice versa) might indicate
        # a mistake or fake review
        # if rating and comment:
        #     if rating <= 2 and contains_positive_words(comment):
        #         self.add_error(
        #             None,
        #             'Your comment seems positive but you gave a low rating. '
        #             'Please verify your review.'
        #         )

        return cleaned_data

    # ============================================
    # Save Methods
    # ============================================

    def save(self, commit=True):
        """
        Save the form data to the database.

        Args:
            commit (bool): Whether to commit to database immediately

        Returns:
            Review: The saved review instance

        Note:
            The book and author should be set by the view before calling save(),
            or use save(commit=False) and set them manually.
        """
        review = super().save(commit=commit)

        # TODO: Add post-save actions
        # if commit:
        #     # Notify book author about new review
        #     review.notify_book_author()

        # TODO: Update book's cached average rating
        # from django.db.models import Avg
        # avg = Review.objects.filter(book=review.book).aggregate(Avg('rating'))
        # review.book.cached_average_rating = avg['rating__avg'] or 0.0
        # review.book.cached_review_count = review.book.reviews.count()
        # review.book.save(update_fields=['cached_average_rating', 'cached_review_count'])

        # TODO: Log the review for analytics
        # ReviewAnalytics.objects.create(
        #     review=review,
        #     action='created' if not self.instance.pk else 'updated',
        #     user=self.user,
        #     ip_address=self.request.META.get('REMOTE_ADDR')
        # )

        # TODO: Award badge/points to reviewer
        # if self.user:
        #     award_reviewer_badge(self.user)

        return review

    # ============================================
    # Helper Methods
    # ============================================

    def get_existing_review(self):
        """
        Get the existing review for this user and book (if any).

        Useful for pre-filling the form when editing an existing review.

        Returns:
            Review|None: Existing review or None

        Example:
            >>> existing = form.get_existing_review()
            >>> if existing:
            ...     print(f"Editing review with rating: {existing.rating}")
        """
        if not self.book or not self.user:
            return None

        try:
            user_profile = self.user.profile
        except Exception:
            return None

        return Review.objects.filter(
            book=self.book,
            author=user_profile
        ).first()

    def is_editing_existing_review(self):
        """
        Check if the form is editing an existing review.

        Returns:
            bool: True if editing, False if creating new

        Example:
            >>> if form.is_editing_existing_review():
            ...     button_text = "Update Review"
            ... else:
            ...     button_text = "Submit Review"
        """
        return self.instance and self.instance.pk is not None

    def get_rating_label(self):
        """
        Get a human-readable label for the current rating.

        Returns:
            str: Rating label (e.g., "Excellent", "Poor")

        Example:
            >>> form.cleaned_data['rating'] = 5
            >>> form.get_rating_label()
            'Excellent'
        """
        rating = self.cleaned_data.get('rating') or (self.instance.rating if self.instance.pk else None)

        labels = {
            1: 'Poor',
            2: 'Fair',
            3: 'Good',
            4: 'Very Good',
            5: 'Excellent',
        }

        return labels.get(rating, '')

    @staticmethod
    def get_rating_distribution(book):
        """
        Get the distribution of ratings for a book.

        Returns a dictionary with counts for each star rating (1-5).
        Useful for displaying rating breakdown in templates.

        Args:
            book (Book): The book to analyze

        Returns:
            dict: Rating distribution {1: count, 2: count, ..., 5: count}

        Example:
            >>> distribution = ReviewForm.get_rating_distribution(book)
            >>> distribution[5]
            58  # 58 five-star reviews
        """
        # TODO: Cache this result for performance
        from django.db.models import Count

        distribution = {i: 0 for i in range(1, 6)}
        ratings = Review.objects.filter(book=book).values('rating').annotate(
            count=Count('id')
        )

        for item in ratings:
            distribution[item['rating']] = item['count']

        return distribution

    @staticmethod
    def get_average_rating(book):
        """
        Calculate the average rating for a book.

        Args:
            book (Book): The book to analyze

        Returns:
            float: Average rating (0.0 if no reviews)

        Example:
            >>> avg = ReviewForm.get_average_rating(book)
            >>> avg
            4.3
        """
        # TODO: Use cached value from Book model if available
        from django.db.models import Avg

        result = Review.objects.filter(book=book).aggregate(Avg('rating'))
        return result['rating__avg'] or 0.0

# ============================================
# Additional Form Classes
# ============================================

# TODO: Add form for moderators to manage reviews
# class ReviewModerationForm(forms.ModelForm):
#     """
#     Form for moderators to manage reviews.
#     
#     Allows hiding/deleting inappropriate reviews.
#     Only available to staff users.
#     """
#     class Meta:
#         model = Review
#         fields = ['is_hidden', 'moderation_note']
#         widgets = {
#             'is_hidden': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input',
#             }),
#             'moderation_note': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Reason for moderation action',
#             }),
#         }


# TODO: Add form for reporting reviews
# class ReviewReportForm(forms.Form):
#     """Form for users to report inappropriate reviews."""
#     REASON_CHOICES = [
#         ('spam', 'Spam or advertising'),
#         ('offensive', 'Offensive or inappropriate content'),
#         ('fake', 'Fake or misleading review'),
#         ('irrelevant', 'Not related to the book'),
#         ('other', 'Other reason'),
#     ]
#     
#     reason = forms.ChoiceField(
#         choices=REASON_CHOICES,
#         widget=forms.RadioSelect(attrs={
#             'class': 'form-check-input',
#         })
#     )
#     
#     details = forms.CharField(
#         required=False,
#         widget=forms.Textarea(attrs={
#             'class': 'form-control',
#             'rows': 3,
#             'placeholder': 'Provide additional details (optional)',
#         }),
#         max_length=500
#     )


# TODO: Add form for helpful/not helpful votes
# class ReviewVoteForm(forms.Form):
#     """Form for voting on review helpfulness."""
#     VOTE_CHOICES = [
#         ('helpful', 'Helpful'),
#         ('not_helpful', 'Not Helpful'),
#     ]
#     
#     vote = forms.ChoiceField(
#         choices=VOTE_CHOICES,
#         widget=forms.RadioSelect(attrs={
#             'class': 'form-check-input',
#         })
#     )
