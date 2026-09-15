"""
Views for book-related operations.

Contains classes for displaying, creating, and editing books.
All views use Class-Based Views (CBV) for code consistency.

Classes:
    BookListView    - List of all published books with filtering/search
    BookDetailView  - Book detail page with chapters and reviews
    BookCreateView  - Create a new book (authenticated users)
    BookUpdateView  - Edit an existing book (author only)

Design Decisions:
    - Separate CreateView and UpdateView for clarity (vs. combined view)
    - Permission checks via mixins and manual verification
    - Query optimization to prevent N+1 problems
    - Atomic operations for counters (views, likes)

TODO: Add the following views in future iterations:
    - BookDeleteView       - Soft-delete books
    - BookLikeView         - Toggle like on a book
    - BookPublishView      - Submit book for moderation
    - BookDraftListView    - List user's unpublished books
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Avg, Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from books.forms import BookForm
from books.models import Book, Category, Tag


# ============================================
# Book List View
# ============================================

class BookListView(ListView):
    """
    List of all published books with pagination, filtering, and search.

    GET /

    Context:
        books: QuerySet[Book] - filtered list of books
        page_obj: Page - pagination object
        categories: QuerySet[Category] - approved categories for filter dropdown
        popular_tags: QuerySet[Tag] - top tags for tag cloud
        current_category: str - currently selected category slug
        current_tag: str - currently selected tag slug
        search_query: str - current search query

    Features:
        - Shows only books with is_published=True
        - Sorted by creation date (newest first)
        - Paginated at 12 books per page
        - Query optimization via select_related() and prefetch_related()
        - Annotated with review_count and avg_rating to avoid N+1 queries
        - Supports filtering by category, tag, and search query

    URL Parameters (optional):
        ?category=<slug> - filter by category
        ?tag=<slug> - filter by tag
        ?q=<query> - search by title (case-insensitive)
        ?sort=<field> - sort by field (newest, popular, rating)

    Example URLs:
        /                                          → All books
        /?category=programming                     → Books in Programming
        /?tag=python                               → Books tagged Python
        /?q=django                                 → Search for "django"
        /?category=programming&tag=python&q=web    → Combined filters
    """
    model = Book
    template_name = 'books/book/list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        """
        Return only published books with optimized queries and filters.

        Optimizations:
            - select_related('author', 'category') - JOIN for FK fields
            - prefetch_related('tags') - separate query for M2M
            - annotate() for review_count and avg_rating - avoid N+1

        Filters from URL (optional):
            ?category=<slug> - filter by category
            ?tag=<slug> - filter by tag
            ?q=<query> - search by title (case-insensitive)
            ?sort=<field> - sort by field

        Returns:
            QuerySet: Filtered, optimized, and annotated queryset of books
        """
        # Base queryset with optimizations
        # TODO: Consider using a custom manager for this common query
        # queryset = Book.published.with_related_data()
        queryset = Book.objects.filter(
            is_published=True
        ).select_related(
            'author', 'category'
        ).prefetch_related(
            'tags'
        ).annotate(
            # Annotate to avoid N+1 queries in template
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating'),
            published_chapter_count=Count(
                'chapters',
                filter=Q(chapters__is_published=True)
            )
        )

        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Filter by tag
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Search by title (case-insensitive)
        # TODO: Replace with full-text search (PostgreSQL SearchVector)
        # for better performance and relevance ranking
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)

        # Sorting
        sort = self.request.GET.get('sort', 'newest')
        # TODO: Add more sort options (most reviewed, most liked)
        if sort == 'popular':
            queryset = queryset.order_by('-views', '-created_at')
        elif sort == 'rating':
            queryset = queryset.order_by('-avg_rating', '-review_count')
        else:  # 'newest' (default)
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add filter options and current filter state to context.

        Context additions:
            categories: QuerySet - approved categories for dropdown
            popular_tags: QuerySet - top 20 tags for tag cloud
            current_category: str - selected category slug (for UI highlighting)
            current_tag: str - selected tag slug
            current_sort: str - current sort option
            search_query: str - current search query
            total_books: int - total number of books matching filters

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)

        # Approved categories for filter dropdown
        # TODO: Cache this queryset - it changes rarely
        context['categories'] = Category.objects.filter(
            status=Category.Status.APPROVED
        ).order_by('title')

        # Popular tags for tag cloud
        # TODO: Cache this queryset and invalidate on tag changes
        context['popular_tags'] = Tag.objects.annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        ).filter(
            book_count__gt=0
        ).order_by('-book_count')[:20]

        # Current filter state (for UI highlighting)
        context['current_category'] = self.request.GET.get('category', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['search_query'] = self.request.GET.get('q', '')

        # Total count for "Showing X of Y books" message
        # TODO: This executes a separate COUNT query - consider caching
        context['total_books'] = self.get_queryset().count()

        return context


# ============================================
# Book Detail View
# ============================================

class BookDetailView(DetailView):
    """
    Book detail page with chapters, reviews, and related information.

    GET /book/<slug>/

    Context:
        book: Book - the book object (with annotated fields)
        chapters: QuerySet[Chapter] - published chapters in reading order
        reviews: QuerySet[Review] - book reviews with author data
        user_review: Review|None - current user's review (if exists)
        average_rating: float - book's average rating
        rating_distribution: dict - count of reviews per star (1-5)
        related_books: QuerySet[Book] - books in same category/tags
        can_edit: bool - whether current user can edit this book

    Features:
        - Automatically increments view counter (atomic)
        - Shows only published chapters
        - Checks if current user has left a review
        - Calculates rating distribution for visual breakdown
        - Suggests related books based on category/tags

    Security:
        - Returns 404 for non-existent books
        - Returns 404 for unpublished books (unless user is author/staff)
    """
    model = Book
    template_name = 'books/book/detail.html'
    context_object_name = 'book'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Optimize queries for related models.

        Uses select_related for FK fields and prefetch_related for M2M
        and reverse relations to minimize database queries.

        Returns:
            QuerySet: Optimized queryset
        """
        return Book.objects.select_related(
            'author', 'category'
        ).prefetch_related(
            'tags'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

    def get_object(self, queryset=None):
        """
        Get the book object, increment view counter, and check access.

        Access control:
            - Published books: accessible to everyone
            - Unpublished books: only author and staff can view

        Uses F() for atomic increment - protects against race conditions
        when multiple requests occur simultaneously.

        Returns:
            Book: The book object with incremented views

        Raises:
            Http404: If book doesn't exist or user can't access it
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        book = get_object_or_404(queryset, slug=slug)

        # Access control: unpublished books only visible to author/staff
        # TODO: Consider adding a "preview link" system for sharing drafts
        if not book.is_published:
            user = self.request.user
            if not user.is_authenticated:
                raise Http404("Book not found.")
            if book.author.user != user and not user.is_staff:
                raise Http404("Book not found.")

        # Atomic view increment (prevents race conditions)
        # TODO: Consider moving view tracking to a separate BookView model
        # to track individual user views and prevent duplicate counting
        Book.objects.filter(pk=book.pk).update(views=F('views') + 1)
        book.views += 1  # Update local variable for template

        return book

    def get_context_data(self, **kwargs):
        """
        Add chapters, reviews, and related data to context.

        Context additions:
            chapters: QuerySet - published chapters in reading order
            reviews: QuerySet - all reviews with author data (optimized)
            user_review: Review|None - current user's review (if exists)
            average_rating: float - book's average rating (0.0 if none)
            rating_distribution: dict - {1: count, 2: count, ..., 5: count}
            related_books: QuerySet - up to 4 related books
            can_edit: bool - whether current user can edit this book
            next_chapter: Chapter|None - first unpublished chapter (for author)

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)
        book = self.object

        # Book chapters (only published, in reading order)
        # TODO: Consider caching chapter list for performance
        context['chapters'] = book.chapters.filter(
            is_published=True
        ).order_by('order')

        # Reviews with query optimization
        context['reviews'] = book.reviews.select_related('author').order_by(
            '-created_at'
        )

        # Current user's review (if authenticated)
        context['user_review'] = None
        if self.request.user.is_authenticated:
            # TODO: Handle case where user has no Profile yet
            try:
                context['user_review'] = book.reviews.get(
                    author=self.request.user.profile
                )
            except Exception:
                context['user_review'] = None

        # Average rating (use annotated value if available)
        context['average_rating'] = getattr(book, 'avg_rating', None) or 0.0

        # Rating distribution for visual breakdown (e.g., star histogram)
        # TODO: Cache this result - expensive query
        context['rating_distribution'] = self._get_rating_distribution(book)

        # Related books (same category or shared tags)
        # TODO: Implement more sophisticated recommendation algorithm
        context['related_books'] = self._get_related_books(book)

        # Permission check for edit button
        context['can_edit'] = self._can_edit_book(book)

        # For authors: show next unpublished chapter (if any)
        if self._can_edit_book(book):
            context['next_unpublished_chapter'] = book.chapters.filter(
                is_published=False
            ).order_by('order').first()

        return context

    def _get_rating_distribution(self, book):
        """
        Calculate the distribution of ratings (how many 1-star, 2-star, etc.).

        Args:
            book (Book): The book to analyze

        Returns:
            dict: {1: count, 2: count, ..., 5: count}

        Example:
            >>> self._get_rating_distribution(book)
            {1: 2, 2: 5, 3: 10, 4: 25, 5: 58}
        """
        # TODO: Cache this result per book (invalidate on new review)
        distribution = {i: 0 for i in range(1, 6)}
        ratings = book.reviews.values('rating').annotate(
            count=Count('id')
        )
        for item in ratings:
            distribution[item['rating']] = item['count']
        return distribution

    def _get_related_books(self, book, limit=4):
        """
        Get books related to this one (same category or shared tags).

        Prioritizes:
            1. Books in the same category
            2. Books with shared tags
            3. Excludes the current book

        Args:
            book (Book): The reference book
            limit (int): Maximum number of related books to return

        Returns:
            QuerySet: Related published books
        """
        # TODO: Implement more sophisticated recommendation algorithm
        # Consider: author's other books, user's reading history, etc.
        queryset = Book.objects.filter(
            is_published=True
        ).exclude(
            pk=book.pk
        ).select_related('author', 'category')

        if book.category:
            # Prefer books in the same category
            same_category = queryset.filter(category=book.category)
            if same_category.count() >= limit:
                return same_category.order_by('-views')[:limit]

            # Fill remaining slots with books sharing tags
            remaining = limit - same_category.count()
            if remaining > 0 and book.tags.exists():
                shared_tags = queryset.filter(
                    tags__in=book.tags.all()
                ).exclude(
                    pk__in=same_category.values_list('pk', flat=True)
                ).distinct().order_by('-views')[:remaining]
                return list(same_category.order_by('-views')) + list(shared_tags)

            return same_category.order_by('-views')[:limit]

        # No category - fall back to shared tags
        if book.tags.exists():
            return queryset.filter(
                tags__in=book.tags.all()
            ).distinct().order_by('-views')[:limit]

        # No category, no tags - return most popular books
        return queryset.order_by('-views')[:limit]

    def _can_edit_book(self, book):
        """
        Check if the current user can edit this book.

        Args:
            book (Book): The book to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        # TODO: Handle case where user has no Profile yet
        try:
            return book.author.user == user or user.is_staff
        except Exception:
            return False


# ============================================
# Book Create View
# ============================================

class BookCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new book.

    GET /book/create/     → Show empty form
    POST /book/create/    → Process form and create book

    Context:
        form: BookForm - the book creation form
        is_edit: bool - always False for this view

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Automatically sets the author to current user
        - Auto-generates slug from title (in model's save())
        - Saves ManyToMany fields (tags)
        - Shows success message after creation

    Permissions:
        - Any authenticated user with a Profile can create books

    TODO: Add rate limiting to prevent spam book creation
    TODO: Add draft auto-save via AJAX
    """
    model = Book
    form_class = BookForm
    template_name = 'books/book/form.html'

    def get_context_data(self, **kwargs):
        """Add edit mode flag to context (always False for create)."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        context['page_title'] = 'Create New Book'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Set author to current user's profile
            2. Save the book (slug auto-generated in model's save())
            3. Save ManyToMany fields (tags)
            4. Add success flash message
            5. Redirect to book detail page

        Returns:
            HttpResponse: Redirect to the new book's detail page
        """
        # TODO: Handle case where user has no Profile yet
        # Redirect to profile creation page if needed
        try:
            profile = self.request.user.profile
        except Exception:
            messages.error(
                self.request,
                'Please complete your profile before creating a book.'
            )
            return redirect('accounts:profile_edit')

        # Save but don't commit to DB yet (need to set author first)
        self.object = form.save(commit=False)
        self.object.author = profile

        # Save to DB (slug auto-generated in model's save())
        self.object.save()

        # Save ManyToMany fields (required after save() when commit=False)
        form.save_m2m()

        messages.success(
            self.request,
            f'Book "{self.object.title}" created successfully! '
            'You can now add chapters.'
        )

        # TODO: Trigger async task to notify followers
        # notify_followers_of_new_book.delay(self.object.id)

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful creation."""
        return reverse('books:book_detail', kwargs={'slug': self.object.slug})


# ============================================
# Book Update View
# ============================================

class BookUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit an existing book (author only).

    GET /book/<slug>/edit/     → Show form with current data
    POST /book/<slug>/edit/    → Process form and update book

    Context:
        form: BookForm - the book edit form (pre-filled)
        is_edit: bool - always True for this view
        book: Book - the book being edited

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Only the book's author (or staff) can edit
        - Preserves existing slug unless title changes
        - Saves ManyToMany fields (tags)
        - Shows success message after update

    Security:
        - Returns 403 Forbidden if user is not the author
        - Returns 404 if book doesn't exist

    Permissions:
        - Book author: full edit access
        - Staff users: full edit access
        - Other users: 403 Forbidden

    TODO: Add edit history tracking (who changed what, when)
    TODO: Add field-level edit permissions (e.g., only author can change title)
    """
    model = Book
    form_class = BookForm
    template_name = 'books/book/form.html'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Return queryset optimized for editing.

        Only returns books (no filtering by author here -
        permission check happens in dispatch()).
        """
        return Book.objects.select_related('author', 'category')

    def get_object(self, queryset=None):
        """
        Get the book object with permission check.

        Returns:
            Book: The book to edit

        Raises:
            Http404: If book doesn't exist
            HttpResponseForbidden: If user can't edit this book
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        book = get_object_or_404(queryset, slug=slug)

        # Permission check: only author or staff can edit
        if not self._can_edit_book(book):
            # TODO: Log unauthorized edit attempts for security monitoring
            raise HttpResponseForbidden(
                "You don't have permission to edit this book."
            )

        return book

    def _can_edit_book(self, book):
        """
        Check if the current user can edit this book.

        Args:
            book (Book): The book to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        # TODO: Handle case where user has no Profile yet
        try:
            return book.author.user == user
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        """Add edit mode flag and book to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['page_title'] = f'Edit: {self.object.title}'
        context['book'] = self.object
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Save the updated book
            2. Save ManyToMany fields (tags)
            3. Add success flash message
            4. Redirect to book detail page

        Returns:
            HttpResponse: Redirect to the book's detail page
        """
        # For UpdateView, self.object is already set by get_object()
        self.object = form.save()

        # Note: save_m2m() is handled automatically by ModelForm.save()
        # when commit=True (the default)

        messages.success(
            self.request,
            f'Book "{self.object.title}" updated successfully!'
        )

        # TODO: Trigger async task to re-calculate reading time
        # update_reading_time.delay(self.object.id)

        # TODO: Invalidate cached book data
        # cache.delete(f'book_{self.object.id}')

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful update."""
        return reverse('books:book_detail', kwargs={'slug': self.object.slug})

# ============================================
# Combined Edit View (Alternative Approach)
# ============================================

# TODO: Consider whether to keep separate Create/Update views
# or combine them into a single BookEditView.
#
# Pros of combined view:
#   - Single URL pattern for both actions
#   - Less code duplication
#
# Cons of combined view:
#   - More complex logic (mode detection)
#   - Harder to apply different permissions
#   - Less clear intent
#
# Current decision: Separate views for clarity and security.

# class BookEditView(LoginRequiredMixin, View):
#     """
#     Combined create/edit view (alternative approach).
#
#     Determines mode based on URL parameters:
#         - No slug → create mode
#         - With slug → edit mode
#     """
#     template_name = 'books/book/form.html'
#     form_class = BookForm
#
#     def dispatch(self, request, *args, **kwargs):
#         """Determine mode and set up instance."""
#         self.slug = kwargs.get('slug')
#         if self.slug:
#             # Edit mode
#             self.object = get_object_or_404(Book, slug=self.slug)
#             if not self._can_edit(self.object):
#                 return HttpResponseForbidden()
#         else:
#             # Create mode
#             self.object = None
#         return super().dispatch(request, *args, **kwargs)
#
#     def get(self, request, *args, **kwargs):
#         form = self.form_class(instance=self.object)
#         return self._render(form)
#
#     def post(self, request, *args, **kwargs):
#         form = self.form_class(
#             request.POST,
#             request.FILES,
#             instance=self.object
#         )
#         if form.is_valid():
#             return self._save(form)
#         return self._render(form)
#
#     def _save(self, form):
#         book = form.save(commit=False)
#         if not book.pk:
#             book.author = self.request.user.profile
#         book.save()
#         form.save_m2m()
#         messages.success(self.request, 'Book saved!')
#         return redirect('books:book_detail', slug=book.slug)
#
#     def _render(self, form):
#         return render(self.request, self.template_name, {
#             'form': form,
#             'is_edit': self.object is not None,
#             'book': self.object,
#         })
#
#     def _can_edit(self, book):
#         user = self.request.user
#         return user.is_staff or book.author.user == user


# ============================================
# Helper Functions (Optional)
# ============================================

# TODO: Extract common logic into helper functions

# def get_user_profile_or_redirect(user, redirect_url='accounts:profile_edit'):
#     """
#     Get user's profile or return redirect response if missing.
#
#     Args:
#         user (User): The user to get profile for
#         redirect_url (str): URL name to redirect to if no profile
#
#     Returns:
#         tuple: (profile, redirect_response)
#             - profile: Profile instance or None
#             - redirect_response: HttpResponse redirect or None
#
#     Example:
#         profile, redirect = get_user_profile_or_redirect(request.user)
#         if redirect:
#             return redirect
#         # Use profile...
#     """
#     try:
#         return user.profile, None
#     except Exception:
#         return None, redirect(redirect_url)
