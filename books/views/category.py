"""
Views for category-related operations.

Contains classes for displaying, creating, and editing category requests.
Categories follow a request-approval workflow where users propose categories
and moderators approve/reject them.

Classes:
    CategoryListView    - List of approved categories
    CategoryDetailView  - Category detail page with books
    CategoryCreateView  - Create a new category request
    CategoryUpdateView  - Edit a pending category request (author only)

Workflow:
    1. User creates category request → status: PENDING
    2. Moderator reviews → status: APPROVED or REJECTED
    3. Only APPROVED categories appear in public lists
    4. Only APPROVED categories can be assigned to books

TODO: Add the following views in future iterations:
    - CategoryModerateView   - Approve/reject categories (staff only)
    - CategoryDeleteView     - Delete category requests
    - CategoryPendingListView - List user's pending requests
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from books.forms import CategoryForm
from books.models import Category, Book


# ============================================
# Category List View
# ============================================

class CategoryListView(ListView):
    """
    List of all APPROVED categories with book counts.

    GET /categories/

    Context:
        categories: QuerySet[Category] - approved categories with book counts
        page_obj: Page - pagination object
        total_categories: int - total number of approved categories

    Features:
        - Shows only categories with status=APPROVED
        - Sorted by name (alphabetical)
        - Annotated with book_count to avoid N+1 queries
        - Paginated at 20 categories per page
        - Query optimization via annotate()

    URL Parameters (optional):
        ?sort=<field> - sort by field (name, popular, recent)
        ?q=<query> - search by category name

    Example URLs:
        /categories/                    → All approved categories
        /categories/?sort=popular       → Sorted by book count
        /categories/?q=python           → Search for "python"
    """
    model = Category
    template_name = 'books/category/list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        """
        Return only approved categories with book counts.

        Optimizations:
            - annotate(book_count=...) - avoid N+1 queries
            - filter(status=APPROVED) - only show approved categories

        Filters from URL (optional):
            ?sort=<field> - sort by field (name, popular, recent)
            ?q=<query> - search by category name

        Returns:
            QuerySet: Filtered, optimized, and annotated queryset
        """
        # Base queryset with optimizations
        # TODO: Consider caching this queryset - categories change rarely
        queryset = Category.objects.filter(
            status=Category.Status.APPROVED
        ).annotate(
            # Count only published books in this category
            book_count=Count(
                'books',
                filter=Q(books__is_published=True)
            )
        )

        # Search by name (case-insensitive)
        # TODO: Replace with full-text search for better performance
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)

        # Sorting
        sort = self.request.GET.get('sort', 'name')
        if sort == 'popular':
            queryset = queryset.order_by('-book_count', 'title')
        elif sort == 'recent':
            queryset = queryset.order_by('-created_at')
        else:  # 'name' (default)
            queryset = queryset.order_by('title')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add additional context for the template.

        Context additions:
            total_categories: int - total number of approved categories
            current_sort: str - current sort option
            search_query: str - current search query

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)

        # Total count for "Showing X of Y categories" message
        # TODO: Cache this count for performance
        context['total_categories'] = self.get_queryset().count()

        # Current filter state (for UI highlighting)
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['search_query'] = self.request.GET.get('q', '')

        # Add popular categories (top 10 by book count)
        # TODO: Cache this queryset
        context['popular_categories'] = Category.objects.filter(
            status=Category.Status.APPROVED
        ).annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        ).order_by('-book_count')[:10]

        return context


# ============================================
# Category Detail View
# ============================================

class CategoryDetailView(DetailView):
    """
    Category detail page with list of books in this category.

    GET /category/<slug>/

    Context:
        category: Category - the category object
        books: QuerySet[Book] - published books in this category
        book_count: int - total number of books
        can_edit: bool - whether current user can edit this category

    Features:
        - Shows only published books in this category
        - Books sorted by creation date (newest first)
        - Query optimization via select_related() and prefetch_related()
        - Annotated with review stats to avoid N+1 queries

    Security:
        - Returns 404 for non-existent categories
        - Returns 404 for non-approved categories (unless author/staff)
    """
    model = Category
    template_name = 'books/category/detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Optimize queries for related models.

        Returns:
            QuerySet: Optimized queryset
        """
        return Category.objects.all()

    def get_object(self, queryset=None):
        """
        Get the category object and check access.

        Access control:
            - Approved categories: accessible to everyone
            - Pending/Rejected categories: only author and staff can view

        Returns:
            Category: The category object

        Raises:
            Http404: If category doesn't exist or user can't access it
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        category = get_object_or_404(queryset, slug=slug)

        # Access control: non-approved categories only visible to author/staff
        if not category.is_approved:
            user = self.request.user
            if not user.is_authenticated:
                raise Http404("Category not found.")
            if category.author.user != user and not user.is_staff:
                raise Http404("Category not found.")

        return category

    def get_context_data(self, **kwargs):
        """
        Add books and related data to context.

        Context additions:
            books: QuerySet - published books in this category (optimized)
            book_count: int - total number of published books
            can_edit: bool - whether current user can edit this category
            related_categories: QuerySet - other categories (for sidebar)

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)
        category = self.object

        # Books in this category (only published, with optimizations)
        # TODO: Add pagination for books if category has many books
        context['books'] = Book.objects.filter(
            category=category,
            is_published=True
        ).select_related(
            'author'
        ).prefetch_related(
            'tags'
        ).annotate(
            review_count=Count('reviews'),
            avg_rating=Count('reviews__rating')  # TODO: Fix to use Avg
        ).order_by('-created_at')

        # Total book count
        context['book_count'] = context['books'].count()

        # Permission check for edit button
        context['can_edit'] = self._can_edit_category(category)

        # Related categories (other approved categories)
        # TODO: Implement better "related" logic based on book overlap
        context['related_categories'] = Category.objects.filter(
            status=Category.Status.APPROVED
        ).exclude(
            pk=category.pk
        ).annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        ).order_by('-book_count')[:10]

        return context

    def _can_edit_category(self, category):
        """
        Check if the current user can edit this category.

        Args:
            category (Category): The category to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        # Only author can edit their own pending requests
        try:
            return (
                    category.author.user == user and
                    category.is_pending
            )
        except Exception:
            return False


# ============================================
# Category Create View
# ============================================

class CategoryCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new category request.

    GET /category/create/     → Show empty form
    POST /category/create/    → Process form and create request

    Context:
        form: CategoryForm - the category creation form
        is_edit: bool - always False for this view

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Automatically sets the author to current user
        - Sets status to PENDING (awaiting moderation)
        - Auto-generates slug from title (in model's save())
        - Shows success message after creation

    Permissions:
        - Any authenticated user with a Profile can create requests

    Workflow:
        1. User fills form → Category created with status=PENDING
        2. Moderator reviews → status changes to APPROVED or REJECTED
        3. User notified of decision

    TODO: Add rate limiting to prevent spam category requests
    TODO: Add AJAX endpoint to check category name availability
    """
    model = Category
    form_class = CategoryForm
    template_name = 'books/category/form.html'

    def get_context_data(self, **kwargs):
        """Add edit mode flag to context (always False for create)."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        context['page_title'] = 'Request New Category'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Set author to current user's profile
            2. Set status to PENDING (awaiting moderation)
            3. Save the category (slug auto-generated in model's save())
            4. Add success flash message
            5. Redirect to category list page

        Returns:
            HttpResponse: Redirect to category list page
        """
        # TODO: Handle case where user has no Profile yet
        try:
            profile = self.request.user.profile
        except Exception:
            messages.error(
                self.request,
                'Please complete your profile before requesting a category.'
            )
            return redirect('accounts:profile_edit')

        # Save but don't commit to DB yet (need to set author and status)
        category = form.save(commit=False)
        category.author = profile
        category.status = Category.Status.PENDING  # Explicitly set status

        # Save to DB (slug auto-generated in model's save())
        category.save()

        messages.success(
            self.request,
            f'Category request "{category.title}" submitted successfully! '
            'A moderator will review your request soon.'
        )

        # TODO: Trigger async task to notify moderators
        # notify_moderators_of_new_category.delay(category.id)

        # TODO: Log the action for audit purposes
        # CategoryAuditLog.objects.create(
        #     category=category,
        #     action='created',
        #     user=self.request.user,
        # )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful creation."""
        # Redirect to category list or user's pending requests
        # TODO: Create a "My Requests" page for users to track their requests
        return reverse('books:category_list')


# ============================================
# Category Update View
# ============================================

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit a pending category request (author only).

    GET /category/<slug>/edit/     → Show form with current data
    POST /category/<slug>/edit/    → Process form and update request

    Context:
        form: CategoryForm - the category edit form (pre-filled)
        is_edit: bool - always True for this view
        category: Category - the category being edited

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Only the category's author can edit (and only if PENDING)
        - Preserves existing slug unless title changes
        - Shows success message after update

    Security:
        - Returns 403 Forbidden if user is not the author
        - Returns 404 if category doesn't exist
        - Only allows editing if status is PENDING

    Permissions:
        - Category author: can edit only if status=PENDING
        - Staff users: can edit any category
        - Other users: 403 Forbidden

    TODO: Add edit history tracking (who changed what, when)
    """
    model = Category
    form_class = CategoryForm
    template_name = 'books/category/form.html'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Return queryset optimized for editing.

        Returns:
            QuerySet: All categories (permission check in get_object)
        """
        return Category.objects.all()

    def get_object(self, queryset=None):
        """
        Get the category object with permission check.

        Returns:
            Category: The category to edit

        Raises:
            Http404: If category doesn't exist
            HttpResponseForbidden: If user can't edit this category
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        category = get_object_or_404(queryset, slug=slug)

        # Permission check: only author (if pending) or staff can edit
        if not self._can_edit_category(category):
            # TODO: Log unauthorized edit attempts for security monitoring
            if not category.is_pending:
                messages.error(
                    self.request,
                    'This category request has already been reviewed and cannot be edited.'
                )
            raise HttpResponseForbidden(
                "You don't have permission to edit this category."
            )

        return category

    def _can_edit_category(self, category):
        """
        Check if the current user can edit this category.

        Args:
            category (Category): The category to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        # Only author can edit, and only if status is PENDING
        try:
            return (
                    category.author.user == user and
                    category.is_pending
            )
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        """Add edit mode flag and category to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['page_title'] = f'Edit Category Request: {self.object.title}'
        context['category'] = self.object
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Save the updated category
            2. Add success flash message
            3. Redirect to category detail page

        Returns:
            HttpResponse: Redirect to the category's detail page
        """
        # For UpdateView, self.object is already set by get_object()
        self.object = form.save()

        messages.success(
            self.request,
            f'Category request "{self.object.title}" updated successfully!'
        )

        # TODO: Invalidate cached category data
        # cache.delete(f'category_{self.object.id}')

        # TODO: Log the edit action
        # CategoryAuditLog.objects.create(
        #     category=self.object,
        #     action='updated',
        #     user=self.request.user,
        # )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful update."""
        return reverse('books:category_detail', kwargs={'slug': self.object.slug})

# ============================================
# Category Moderate View (Staff Only)
# ============================================

# TODO: Implement this view for moderators
# class CategoryModerateView(LoginRequiredMixin, UpdateView):
#     """
#     Approve or reject a category request (staff only).
#
#     GET /category/<slug>/moderate/     → Show moderation form
#     POST /category/<slug>/moderate/    → Process approval/rejection
#
#     Features:
#         - Requires staff permission
#         - Allows changing status to APPROVED or REJECTED
#         - Requires rejection reason if rejecting
#         - Notifies the category author of the decision
#
#     Permissions:
#         - Staff users only
#         - Other users: 403 Forbidden
#     """
#     model = Category
#     form_class = CategoryModerationForm  # TODO: Create this form
#     template_name = 'books/category/moderate.html'
#     slug_url_kwarg = 'slug'
#
#     def dispatch(self, request, *args, **kwargs):
#         """Check if user is staff."""
#         if not request.user.is_staff:
#             return HttpResponseForbidden("Staff access required.")
#         return super().dispatch(request, *args, **kwargs)
#
#     def form_valid(self, form):
#         """Handle approval/rejection."""
#         category = form.save(commit=False)
#
#         # Set reviewer
#         category.reviewed_by = self.request.user.profile
#
#         # Validate rejection reason
#         if category.status == Category.Status.REJECTED:
#             if not category.rejection_reason:
#                 form.add_error(
#                     'rejection_reason',
#                     'Please provide a reason for rejection.'
#                 )
#                 return self.form_invalid(form)
#
#         category.save()
#
#         # Notify the author
#         # TODO: Implement notification system
#         # notify_category_author(category)
#
#         messages.success(
#             self.request,
#             f'Category "{category.title}" has been {category.get_status_display().lower()}.'
#         )
#
#         return redirect('books:category_pending_list')


# ============================================
# Helper Functions
# ============================================

# TODO: Add helper functions for common operations

# def get_category_or_404_with_access_check(slug, user):
#     """
#     Get a category with access control.
#
#     Args:
#         slug (str): Category slug
#         user (User): Current user
#
#     Returns:
#         Category: The category object
#
#     Raises:
#         Http404: If category doesn't exist or user can't access it
#     """
#     category = get_object_or_404(Category, slug=slug)
#
#     if not category.is_approved:
#         if not user.is_authenticated:
#             raise Http404("Category not found.")
#         if category.author.user != user and not user.is_staff:
#             raise Http404("Category not found.")
#
#     return category
