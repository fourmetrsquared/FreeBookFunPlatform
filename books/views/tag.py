"""
Views for tag-related operations.

Contains classes for displaying, creating, and editing tags.
Tags provide flexible, user-generated classification for books.

Classes:
    TagListView    - List of all tags with book counts
    TagDetailView  - Tag detail page with books
    TagCreateView  - Create a new tag
    TagUpdateView  - Edit an existing tag (staff only)

Key Features:
    - Tag cloud visualization with book counts
    - Search and filter functionality
    - Permission checks (staff can edit, anyone can create)
    - Query optimization to prevent N+1 problems
    - Popular and trending tags display

Workflow:
    1. Users can create tags when adding books
    2. Tags are automatically normalized (title case)
    3. Tags with books appear in tag cloud
    4. Staff can merge duplicate tags
    5. Readers can browse books by tag

TODO: Add the following views in future iterations:
    - TagDeleteView        - Delete tags (staff only)
    - TagMergeView         - Merge duplicate tags (staff only)
    - TagAutocompleteView  - AJAX autocomplete for tag input
    - TagTrendingView      - Show trending tags
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from books.forms import TagForm
from books.models import Tag, Book


# ============================================
# Tag List View
# ============================================

class TagListView(ListView):
    """
    List of all tags with book counts and search functionality.

    GET /tags/

    Context:
        tags: QuerySet[Tag] - tags with book counts
        page_obj: Page - pagination object
        total_tags: int - total number of tags
        popular_tags: QuerySet[Tag] - top 20 tags by book count
        tag_cloud: list - tags sized for cloud visualization

    Features:
        - Shows tags with at least 1 book
        - Annotated with book_count to avoid N+1 queries
        - Sorted by popularity (book count) or alphabetically
        - Search functionality by tag name
        - Tag cloud visualization data
        - Paginated at 50 tags per page

    URL Parameters (optional):
        ?sort=<field> - sort by field (popular, name, recent)
        ?q=<query> - search by tag name
        ?min_books=<int> - minimum book count filter

    Example URLs:
        /tags/                          → All tags (sorted by popularity)
        /tags/?sort=name                → Sorted alphabetically
        /tags/?q=python                 → Search for "python"
        /tags/?min_books=5              → Tags with 5+ books
    """
    model = Tag
    template_name = 'books/tag/list.html'
    context_object_name = 'tags'
    paginate_by = 50

    def get_queryset(self):
        """
        Return tags with book counts and optional filters.

        Optimizations:
            - annotate(book_count=...) - avoid N+1 queries
            - filter(book_count__gt=0) - only show tags with books

        Filters from URL (optional):
            ?sort=<field> - sort by field (popular, name, recent)
            ?q=<query> - search by tag name
            ?min_books=<int> - minimum book count filter

        Returns:
            QuerySet: Filtered, optimized, and annotated queryset of tags
        """
        # Base queryset with optimizations
        # TODO: Consider caching this queryset - tags change rarely
        queryset = Tag.objects.annotate(
            # Count only published books with this tag
            book_count=Count(
                'books',
                filter=Q(books__is_published=True)
            )
        ).filter(
            book_count__gt=0  # Only show tags with at least 1 book
        )

        # Search by name (case-insensitive)
        # TODO: Replace with full-text search for better performance
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(name__icontains=query)

        # Minimum book count filter
        min_books = self.request.GET.get('min_books')
        if min_books and min_books.isdigit():
            queryset = queryset.filter(book_count__gte=int(min_books))

        # Sorting
        sort = self.request.GET.get('sort', 'popular')
        if sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == 'recent':
            queryset = queryset.order_by('-created_at')
        else:  # 'popular' (default)
            queryset = queryset.order_by('-book_count', 'name')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add tag cloud data and popular tags to context.

        Context additions:
            total_tags: int - total number of tags with books
            popular_tags: QuerySet - top 20 tags by book count
            tag_cloud: list - tags sized for cloud visualization
            current_sort: str - current sort option
            search_query: str - current search query
            min_books: int - current minimum book filter

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)

        # Total count
        context['total_tags'] = self.get_queryset().count()

        # Popular tags (top 20)
        # TODO: Cache this queryset
        context['popular_tags'] = Tag.objects.annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        ).filter(
            book_count__gt=0
        ).order_by('-book_count')[:20]

        # Tag cloud data (for visualization)
        # TODO: Implement proper tag cloud sizing algorithm
        context['tag_cloud'] = self._get_tag_cloud_data()

        # Current filter state (for UI highlighting)
        context['current_sort'] = self.request.GET.get('sort', 'popular')
        context['search_query'] = self.request.GET.get('q', '')
        context['min_books'] = self.request.GET.get('min_books', '')

        return context

    def _get_tag_cloud_data(self, limit=50):
        """
        Get tag data for cloud visualization.

        Returns tags with book counts and calculated font sizes
        for a tag cloud display.

        Args:
            limit (int): Maximum number of tags to include

        Returns:
            list: Tags with 'font_size' attribute for CSS styling

        TODO: Implement logarithmic sizing algorithm
        TODO: Cache this result for performance
        """
        tags = Tag.objects.annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        ).filter(
            book_count__gt=0
        ).order_by('-book_count')[:limit]

        if not tags:
            return []

        # Simple linear sizing (can be improved with logarithmic scaling)
        max_count = max(tag.book_count for tag in tags)
        min_count = min(tag.book_count for tag in tags)

        tag_cloud = []
        for tag in tags:
            # Calculate font size (12px to 32px range)
            if max_count == min_count:
                font_size = 20
            else:
                ratio = (tag.book_count - min_count) / (max_count - min_count)
                font_size = int(12 + (ratio * 20))

            tag.font_size = font_size
            tag_cloud.append(tag)

        return tag_cloud


# ============================================
# Tag Detail View
# ============================================

class TagDetailView(DetailView):
    """
    Tag detail page with list of books tagged with this tag.

    GET /tag/<slug>/

    Context:
        tag: Tag - the tag object
        books: QuerySet[Book] - published books with this tag
        book_count: int - total number of books
        related_tags: QuerySet[Tag] - tags that frequently appear together

    Features:
        - Shows only published books with this tag
        - Books sorted by creation date (newest first)
        - Query optimization via select_related() and prefetch_related()
        - Annotated with review stats to avoid N+1 queries
        - Shows related tags (co-occurrence analysis)

    Security:
        - Returns 404 for non-existent tags
    """
    model = Tag
    template_name = 'books/tag/detail.html'
    context_object_name = 'tag'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Optimize queries for related models.

        Returns:
            QuerySet: Optimized queryset
        """
        return Tag.objects.all()

    def get_object(self, queryset=None):
        """
        Get the tag object.

        Returns:
            Tag: The tag object

        Raises:
            Http404: If tag doesn't exist
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(queryset, slug=slug)

    def get_context_data(self, **kwargs):
        """
        Add books and related data to context.

        Context additions:
            books: QuerySet - published books with this tag (optimized)
            book_count: int - total number of published books
            related_tags: QuerySet - tags that frequently appear together
            can_edit: bool - whether current user can edit this tag

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)
        tag = self.object

        # Books with this tag (only published, with optimizations)
        # TODO: Add pagination for books if tag has many books
        context['books'] = Book.objects.filter(
            tags=tag,
            is_published=True
        ).select_related(
            'author', 'category'
        ).prefetch_related(
            'tags'
        ).annotate(
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        ).order_by('-created_at')

        # Total book count
        context['book_count'] = context['books'].count()

        # Related tags (tags that frequently appear with this tag)
        # TODO: Implement co-occurrence analysis
        context['related_tags'] = self._get_related_tags(tag)

        # Permission check for edit button
        context['can_edit'] = self.request.user.is_staff

        return context

    def _get_related_tags(self, tag, limit=10):
        """
        Get tags that frequently appear together with this tag.

        Uses co-occurrence analysis to find related tags.

        Args:
            tag (Tag): The reference tag
            limit (int): Maximum number of related tags to return

        Returns:
            QuerySet: Related tags with co_occurrence count

        TODO: Cache this result for performance
        TODO: Implement more sophisticated algorithm
        """
        # Get all books with this tag
        book_ids = Book.objects.filter(
            tags=tag,
            is_published=True
        ).values_list('id', flat=True)

        # Find other tags that appear in these books
        related_tags = Tag.objects.filter(
            books__id__in=book_ids
        ).exclude(
            pk=tag.pk
        ).annotate(
            co_occurrence=Count('books', filter=Q(books__id__in=book_ids))
        ).order_by('-co_occurrence')[:limit]

        return related_tags


# ============================================
# Tag Create View
# ============================================

class TagCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new tag.

    GET /tag/create/     → Show empty form
    POST /tag/create/    → Process form and create tag

    Context:
        form: TagForm - the tag creation form
        is_edit: bool - always False for this view
        similar_tags: QuerySet - existing similar tags (for suggestions)

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Auto-generates slug from name (in model's save())
        - Normalizes tag name (title case)
        - Checks for duplicate names (case-insensitive)
        - Shows similar existing tags as suggestions
        - Shows success message after creation

    Permissions:
        - Any authenticated user can create tags

    TODO: Add rate limiting to prevent spam tag creation
    TODO: Add AJAX endpoint to check tag name availability
    """
    model = Tag
    form_class = TagForm
    template_name = 'books/tag/form.html'

    def get_form_kwargs(self):
        """
        Pass the user to the form for validation.

        Returns:
            dict: Form kwargs with user parameter
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add edit mode flag and similar tags to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        context['page_title'] = 'Create New Tag'

        # Show similar existing tags as suggestions
        # TODO: Implement this via AJAX for real-time suggestions
        context['similar_tags'] = Tag.objects.annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        ).filter(
            book_count__gt=0
        ).order_by('-book_count')[:10]

        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Save the tag (slug auto-generated in model's save())
            2. Add success flash message
            3. Redirect to tag detail page

        Returns:
            HttpResponse: Redirect to the new tag's detail page
        """
        # Save to DB (slug auto-generated in model's save())
        self.object = form.save()

        messages.success(
            self.request,
            f'Tag "{self.object.name}" created successfully!'
        )

        # TODO: Log the action for audit purposes
        # TagAuditLog.objects.create(
        #     tag=self.object,
        #     action='created',
        #     user=self.request.user,
        # )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful creation."""
        return reverse('books:tag_detail', kwargs={'slug': self.object.slug})


# ============================================
# Tag Update View (Staff Only)
# ============================================

class TagUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Edit an existing tag (staff only).

    GET /tag/<slug>/edit/     → Show form with current data
    POST /tag/<slug>/edit/    → Process form and update tag

    Context:
        form: TagForm - the tag edit form (pre-filled)
        tag: Tag - the tag being edited
        is_edit: bool - always True for this view

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Requires staff permission (UserPassesTestMixin)
        - Preserves existing slug unless name changes
        - Shows success message after update

    Security:
        - Returns 403 Forbidden if user is not staff
        - Returns 404 if tag doesn't exist

    Permissions:
        - Staff users only: full edit access
        - Other users: 403 Forbidden

    TODO: Add edit history tracking (who changed what, when)
    TODO: Add redirect old slug to new slug after rename
    """
    model = Tag
    form_class = TagForm
    template_name = 'books/tag/form.html'
    slug_url_kwarg = 'slug'

    def test_func(self):
        """
        Check if user is staff.

        Returns:
            bool: True if user is staff, False otherwise
        """
        return self.request.user.is_staff

    def get_queryset(self):
        """
        Return queryset optimized for editing.

        Returns:
            QuerySet: All tags
        """
        return Tag.objects.all()

    def get_object(self, queryset=None):
        """
        Get the tag object.

        Returns:
            Tag: The tag to edit

        Raises:
            Http404: If tag doesn't exist
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(queryset, slug=slug)

    def get_form_kwargs(self):
        """
        Pass the user to the form for validation.

        Returns:
            dict: Form kwargs with user parameter
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add tag and edit mode flag to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['tag'] = self.object
        context['page_title'] = f'Edit Tag: {self.object.name}'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Save the updated tag
            2. Add success flash message
            3. Redirect to tag detail page

        Returns:
            HttpResponse: Redirect to the tag's detail page
        """
        # Store old slug for potential redirect
        old_slug = self.object.slug

        # Save the updated tag
        self.object = form.save()

        messages.success(
            self.request,
            f'Tag "{self.object.name}" updated successfully!'
        )

        # TODO: Create redirect from old slug to new slug
        # if old_slug != self.object.slug:
        #     TagRedirect.objects.create(
        #         old_slug=old_slug,
        #         new_tag=self.object
        #     )

        # TODO: Log the edit action
        # TagAuditLog.objects.create(
        #     tag=self.object,
        #     action='updated',
        #     user=self.request.user,
        # )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful update."""
        return reverse('books:tag_detail', kwargs={'slug': self.object.slug})

# ============================================
# Tag Autocomplete View (AJAX)
# ============================================

# TODO: Implement this view for AJAX autocomplete
# class TagAutocompleteView(View):
#     """
#     AJAX endpoint for tag autocomplete.
#
#     GET /api/tags/autocomplete/?q=<query>
#
#     Returns:
#         JsonResponse: List of matching tags
#
#     Example response:
#         {
#             "results": [
#                 {"id": 1, "name": "Python", "book_count": 42},
#                 {"id": 2, "name": "Django", "book_count": 28}
#             ]
#         }
#     """
#     def get(self, request, *args, **kwargs):
#         query = request.GET.get('q', '').strip()
#
#         if len(query) < 2:
#             return JsonResponse({'results': []})
#
#         # Search for matching tags
#         tags = Tag.objects.filter(
#             name__icontains=query
#         ).annotate(
#             book_count=Count('books', filter=Q(books__is_published=True))
#         ).filter(
#             book_count__gt=0
#         ).order_by('-book_count')[:10]
#
#         results = [
#             {
#                 'id': tag.id,
#                 'name': tag.name,
#                 'book_count': tag.book_count
#             }
#             for tag in tags
#         ]
#
#         return JsonResponse({'results': results})


# ============================================
# Tag Merge View (Staff Only)
# ============================================

# TODO: Implement this view for tag merging
# class TagMergeView(LoginRequiredMixin, UserPassesTestMixin, FormView):
#     """
#     Merge two tags into one (staff only).
#
#     GET /tag/merge/     → Show merge form
#     POST /tag/merge/    → Process merge
#
#     Features:
#         - Requires staff permission
#         - Moves all books from source tag to target tag
#         - Deletes source tag after merge
#         - Shows confirmation before merge
#
#     Permissions:
#         - Staff users only
#     """
#     template_name = 'books/tag/merge.html'
#     form_class = TagMergeForm  # TODO: Create this form
#
#     def test_func(self):
#         return self.request.user.is_staff
#
#     def form_valid(self, form):
#         source_tag = form.cleaned_data['source_tag']
#         target_tag = form.cleaned_data['target_tag']
#
#         # Merge tags
#         target_tag.merge_with(source_tag)
#
#         messages.success(
#             self.request,
#             f'Tag "{source_tag.name}" merged into "{target_tag.name}".'
#         )
#
#         # TODO: Log the merge action
#         # TagAuditLog.objects.create(
#         #     tag=target_tag,
#         #     action='merged',
#         #     details=f'Merged from: {source_tag.name}',
#         #     user=self.request.user,
#         # )
#
#         return redirect('books:tag_detail', slug=target_tag.slug)


# ============================================
# Helper Functions
# ============================================

# TODO: Add helper functions for common operations

# def get_tag_or_404(slug):
#     """
#     Get a tag with book count annotation.
#
#     Args:
#         slug (str): Tag slug
#
#     Returns:
#         Tag: The tag object with book_count attribute
#
#     Raises:
#         Http404: If tag doesn't exist
#     """
#     return get_object_or_404(
#         Tag.objects.annotate(
#             book_count=Count('books', filter=Q(books__is_published=True))
#         ),
#         slug=slug
#     )


# def suggest_similar_tags(tag_name, limit=5):
#     """
#     Suggest existing tags similar to the given name.
#
#     Args:
#         tag_name (str): The tag name to match
#         limit (int): Maximum number of suggestions
#
#     Returns:
#         QuerySet: Similar tags
#
#     TODO: Implement fuzzy matching for better suggestions
#     TODO: Use PostgreSQL trigram similarity for advanced matching
#     """
#     return Tag.objects.filter(
#         name__icontains=tag_name
#     ).annotate(
#         book_count=Count('books', filter=Q(books__is_published=True))
#     ).order_by('-book_count')[:limit]
