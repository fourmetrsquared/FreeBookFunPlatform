"""
Views for review-related operations.

Contains classes for displaying, creating, and editing book reviews.
Reviews allow readers to rate books (1-5 stars) and share feedback.

Classes:
    ReviewListView    - List of all reviews (for moderation/overview)
    ReviewDetailView  - Review detail page
    ReviewCreateView  - Create a new review for a book
    ReviewUpdateView  - Edit an existing review (author only)

Key Features:
    - 5-star rating system with visual display
    - One review per user per book enforcement
    - Self-review prevention (authors can't review their own books)
    - Permission checks (only review author can edit)
    - Query optimization to prevent N+1 problems
    - Rating distribution and average calculation

Workflow:
    1. Reader browses a book
    2. Reader leaves a review with rating (1-5 stars) and optional comment
    3. Review is immediately visible
    4. Reader can edit their own review later
    5. Book's average rating is updated automatically

TODO: Add the following views in future iterations:
    - ReviewDeleteView       - Delete reviews (author only)
    - ReviewReportView       - Report inappropriate reviews
    - ReviewVoteView         - Mark reviews as helpful/not helpful
    - ReviewModerateView     - Hide/delete reviews (staff only)
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from books.forms import ReviewForm
from books.models import Review, Book


# ============================================
# Review List View
# ============================================

class ReviewListView(ListView):
    """
    List of all reviews with pagination and filtering.

    GET /reviews/

    Context:
        reviews: QuerySet[Review] - all reviews with author and book data
        page_obj: Page - pagination object
        total_reviews: int - total number of reviews
        average_rating: float - average rating across all reviews

    Features:
        - Shows all reviews (for moderation/overview)
        - Sorted by creation date (newest first)
        - Query optimization via select_related()
        - Paginated at 20 reviews per page
        - Annotated with book and author data

    URL Parameters (optional):
        ?book=<slug> - filter by book
        ?rating=<1-5> - filter by rating
        ?sort=<field> - sort by field (newest, rating, helpful)

    Example URLs:
        /reviews/                          → All reviews
        /reviews/?book=learning-django     → Reviews for specific book
        /reviews/?rating=5                 → Only 5-star reviews
    """
    model = Review
    template_name = 'books/review/list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        """
        Return all reviews with optimized queries.

        Optimizations:
            - select_related('book', 'author') - JOIN for FK fields
            - annotate() for additional data

        Filters from URL (optional):
            ?book=<slug> - filter by book
            ?rating=<1-5> - filter by rating
            ?sort=<field> - sort by field

        Returns:
            QuerySet: Filtered and optimized queryset of reviews
        """
        # Base queryset with optimizations
        queryset = Review.objects.select_related(
            'book', 'author'
        )

        # Filter by book
        book_slug = self.request.GET.get('book')
        if book_slug:
            queryset = queryset.filter(book__slug=book_slug)

        # Filter by rating
        rating = self.request.GET.get('rating')
        if rating and rating.isdigit():
            queryset = queryset.filter(rating=int(rating))

        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'rating':
            queryset = queryset.order_by('-rating', '-created_at')
        # TODO: Add 'helpful' sorting when ReviewVote model is implemented
        # elif sort == 'helpful':
        #     queryset = queryset.annotate(
        #         helpful_count=Count('votes', filter=Q(votes__vote_type='helpful'))
        #     ).order_by('-helpful_count')
        else:  # 'newest' (default)
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add additional context for the template.

        Context additions:
            total_reviews: int - total number of reviews
            average_rating: float - average rating across all reviews
            rating_distribution: dict - count of reviews per star (1-5)
            current_book: str - currently selected book slug
            current_rating: str - currently selected rating
            current_sort: str - current sort option

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)

        # Total count
        context['total_reviews'] = self.get_queryset().count()

        # Average rating across all reviews
        # TODO: Cache this for performance
        context['average_rating'] = Review.objects.aggregate(
            avg=Avg('rating')
        )['avg'] or 0.0

        # Rating distribution
        # TODO: Cache this for performance
        context['rating_distribution'] = self._get_rating_distribution()

        # Current filter state (for UI highlighting)
        context['current_book'] = self.request.GET.get('book', '')
        context['current_rating'] = self.request.GET.get('rating', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')

        return context

    def _get_rating_distribution(self):
        """
        Calculate the distribution of ratings across all reviews.

        Returns:
            dict: {1: count, 2: count, ..., 5: count}
        """
        distribution = {i: 0 for i in range(1, 6)}
        ratings = Review.objects.values('rating').annotate(
            count=Count('id')
        )
        for item in ratings:
            distribution[item['rating']] = item['count']
        return distribution


# ============================================
# Review Detail View
# ============================================

class ReviewDetailView(DetailView):
    """
    Review detail page with full content.

    GET /review/<pk>/

    Context:
        review: Review - the review object
        book: Book - the reviewed book
        can_edit: bool - whether current user can edit this review
        rating_percentage: int - rating as percentage (0-100)

    Features:
        - Shows full review content
        - Displays star rating visually
        - Shows book information
        - Query optimization via select_related()

    Security:
        - Returns 404 for non-existent reviews
    """
    model = Review
    template_name = 'books/review/detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        """
        Optimize queries for related models.

        Returns:
            QuerySet: Optimized queryset
        """
        return Review.objects.select_related('book', 'author')

    def get_context_data(self, **kwargs):
        """
        Add book and permissions to context.

        Context additions:
            book: Book - the reviewed book
            can_edit: bool - whether current user can edit this review
            rating_percentage: int - rating as percentage (0-100)
            star_icons: str - HTML star icons for the rating

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)
        review = self.object

        # Reviewed book
        context['book'] = review.book

        # Permission check for edit button
        context['can_edit'] = self._can_edit_review(review)

        # Rating as percentage (for progress bars)
        context['rating_percentage'] = (review.rating / 5) * 100

        # Star icons HTML
        context['star_icons'] = '★' * review.rating + '☆' * (5 - review.rating)

        return context

    def _can_edit_review(self, review):
        """
        Check if the current user can edit this review.

        Args:
            review (Review): The review to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        try:
            return review.author.user == user
        except Exception:
            return False


# ============================================
# Review Create View
# ============================================

class ReviewCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new review for a book.

    GET /book/<book_slug>/review/create/     → Show empty form
    POST /book/<book_slug>/review/create/    → Process form and create review

    Context:
        form: ReviewForm - the review creation form
        book: Book - the book being reviewed
        is_edit: bool - always False for this view
        existing_review: Review|None - user's existing review (if any)

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Automatically sets the author to current user
        - Prevents duplicate reviews (one per user per book)
        - Prevents self-reviews (author can't review own book)
        - Shows success message after creation

    Permissions:
        - Any authenticated user with a Profile can create reviews
        - Except the book's author (no self-reviews)

    Workflow:
        1. User navigates to book detail page
        2. User clicks "Write Review"
        3. User fills form with rating and comment
        4. Review is created and immediately visible
        5. Book's average rating is updated

    Security:
        - Returns 403 if user tries to review their own book
        - Redirects to edit page if user already reviewed the book
    """
    model = Review
    form_class = ReviewForm
    template_name = 'books/review/form.html'

    def get_book(self):
        """
        Get the book from URL parameter.

        Returns:
            Book: The book being reviewed

        Raises:
            Http404: If book doesn't exist
        """
        book_slug = self.kwargs.get('book_slug')
        return get_object_or_404(Book, slug=book_slug)

    def dispatch(self, request, *args, **kwargs):
        """
        Check permissions before allowing access.

        Prevents:
            - Self-reviews (author can't review own book)
            - Duplicate reviews (redirects to edit if exists)

        Returns:
            HttpResponse: Redirect or normal response
        """
        self.book = self.get_book()

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Get user's profile
        try:
            user_profile = request.user.profile
        except Exception:
            messages.error(
                request,
                'Please complete your profile before leaving reviews.'
            )
            return redirect('accounts:profile_edit')

        # Prevent self-reviews
        if self.book.author_id == user_profile.id:
            messages.warning(
                request,
                'You cannot review your own book. '
                'Please let others share their feedback!'
            )
            return redirect('books:book_detail', slug=self.book.slug)

        # Check for existing review
        existing_review = Review.objects.filter(
            book=self.book,
            author=user_profile
        ).first()

        if existing_review:
            messages.info(
                request,
                'You have already reviewed this book. '
                'You can edit your existing review.'
            )
            return redirect('books:review_edit', pk=existing_review.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Pass the book and user to the form for validation.

        Returns:
            dict: Form kwargs with book and user parameters
        """
        kwargs = super().get_form_kwargs()
        kwargs['book'] = self.book
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add book and edit mode flag to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        context['book'] = self.book
        context['page_title'] = f'Write Review for: {self.book.title}'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Set book from URL parameter
            2. Set author to current user's profile
            3. Save the review
            4. Add success flash message
            5. Redirect to book detail page

        Returns:
            HttpResponse: Redirect to the book's detail page
        """
        # Get user's profile
        try:
            profile = self.request.user.profile
        except Exception:
            messages.error(
                self.request,
                'Please complete your profile before leaving reviews.'
            )
            return redirect('accounts:profile_edit')

        # Save but don't commit to DB yet (need to set book and author)
        self.object = form.save(commit=False)
        self.object.book = self.book
        self.object.author = profile

        # Save to DB
        self.object.save()

        messages.success(
            self.request,
            'Thank you for your review! Your feedback helps other readers.'
        )

        # TODO: Trigger async task to notify book author
        # notify_book_author_of_review.delay(self.object.id)

        # TODO: Update book's cached average rating
        # update_book_rating_cache.delay(self.book.id)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful creation."""
        return reverse('books:book_detail', kwargs={'slug': self.book.slug})


# ============================================
# Review Update View
# ============================================

class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit an existing review (author only).

    GET /review/<pk>/edit/     → Show form with current data
    POST /review/<pk>/edit/    → Process form and update review

    Context:
        form: ReviewForm - the review edit form (pre-filled)
        review: Review - the review being edited
        book: Book - the reviewed book
        is_edit: bool - always True for this view

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Only the review's author (or staff) can edit
        - Shows success message after update

    Security:
        - Returns 403 Forbidden if user is not the review author
        - Returns 404 if review doesn't exist

    Permissions:
        - Review author: full edit access
        - Staff users: full edit access
        - Other users: 403 Forbidden

    TODO: Add time-based edit restriction (e.g., can only edit within 24 hours)
    TODO: Add edit history tracking (who changed what, when)
    """
    model = Review
    form_class = ReviewForm
    template_name = 'books/review/form.html'

    def get_queryset(self):
        """
        Return queryset optimized for editing.

        Returns:
            QuerySet: All reviews (permission check in get_object)
        """
        return Review.objects.select_related('book', 'author')

    def get_object(self, queryset=None):
        """
        Get the review object with permission check.

        Returns:
            Review: The review to edit

        Raises:
            Http404: If review doesn't exist
            HttpResponseForbidden: If user can't edit this review
        """
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get('pk')
        review = get_object_or_404(queryset, pk=pk)

        # Permission check: only review author or staff can edit
        if not self._can_edit_review(review):
            # TODO: Log unauthorized edit attempts for security monitoring
            raise HttpResponseForbidden(
                "You don't have permission to edit this review."
            )

        return review

    def get_form_kwargs(self):
        """
        Pass the book and user to the form for validation.

        Returns:
            dict: Form kwargs with book and user parameters
        """
        kwargs = super().get_form_kwargs()
        kwargs['book'] = self.object.book
        kwargs['user'] = self.request.user
        return kwargs

    def _can_edit_review(self, review):
        """
        Check if the current user can edit this review.

        Args:
            review (Review): The review to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        try:
            return review.author.user == user
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        """Add book, review, and edit mode flag to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['book'] = self.object.book
        context['review'] = self.object
        context['page_title'] = f'Edit Review for: {self.object.book.title}'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Save the updated review
            2. Add success flash message
            3. Redirect to book detail page

        Returns:
            HttpResponse: Redirect to the book's detail page
        """
        # For UpdateView, self.object is already set by get_object()
        self.object = form.save()

        messages.success(
            self.request,
            'Your review has been updated successfully!'
        )

        # TODO: Update book's cached average rating
        # update_book_rating_cache.delay(self.object.book.id)

        # TODO: Invalidate cached review data
        # cache.delete(f'review_{self.object.id}')

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful update."""
        return reverse('books:book_detail', kwargs={'slug': self.object.book.slug})

# ============================================
# Helper Functions
# ============================================

# TODO: Add helper functions for common operations

# def get_review_or_404_with_access_check(pk, user):
#     """
#     Get a review with access control.
#
#     Args:
#         pk (int): Review primary key
#         user (User): Current user
#
#     Returns:
#         Review: The review object
#
#     Raises:
#         Http404: If review doesn't exist
#     """
#     return get_object_or_404(Review, pk=pk)


# def can_user_review_book(user, book):
#     """
#     Check if a user can review a book.
#
#     Args:
#         user (User): The user to check
#         book (Book): The book to review
#
#     Returns:
#         tuple: (can_review, reason)
#             - can_review (bool): True if user can review
#             - reason (str): Reason if can't review
#
#     Example:
#         can_review, reason = can_user_review_book(user, book)
#         if not can_review:
#             messages.error(request, reason)
#     """
#     if not user.is_authenticated:
#         return False, 'You must be logged in to leave a review.'
#
#     try:
#         user_profile = user.profile
#     except Exception:
#         return False, 'Please complete your profile before leaving reviews.'
#
#     if book.author_id == user_profile.id:
#         return False, 'You cannot review your own book.'
#
#     existing_review = Review.objects.filter(
#         book=book,
#         author=user_profile
#     ).exists()
#
#     if existing_review:
#         return False, 'You have already reviewed this book.'
#
#     return True, None
