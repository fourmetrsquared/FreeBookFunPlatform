"""
Views package for the MD Books Library.

This module serves as the public API for all views in the books application.
It imports and exports all view classes, providing a clean interface for
URL configuration and other modules to access views without knowing the
internal file structure.

Public API - Books:
    BookListView        - List all published books with filtering/search
    BookDetailView      - Book detail page with chapters and reviews
    BookCreateView      - Create a new book (authenticated users)
    BookUpdateView      - Edit an existing book (author only)

Public API - Categories:
    CategoryListView    - List all approved categories
    CategoryDetailView  - Category detail page with books
    CategoryCreateView  - Create a new category request
    CategoryUpdateView  - Edit a pending category request (author only)

Public API - Chapters:
    ChapterListView     - List published chapters for a book
    ChapterDetailView   - Chapter detail page with rendered Markdown
    ChapterCreateView   - Create a new chapter (book author only)
    ChapterUpdateView   - Edit an existing chapter (book author only)

Public API - Reviews:
    ReviewListView      - List all reviews with filtering
    ReviewDetailView    - Review detail page
    ReviewCreateView    - Create a new review for a book
    ReviewUpdateView    - Edit an existing review (author only)

Public API - Tags:
    TagListView         - List all tags with book counts and tag cloud
    TagDetailView       - Tag detail page with books
    TagCreateView       - Create a new tag (authenticated users)
    TagUpdateView       - Edit an existing tag (staff only)

Usage in urls.py:
    from books.views import BookListView, BookDetailView

    urlpatterns = [
        path('', BookListView.as_view(), name='book_list'),
        path('book/<slug:slug>/', BookDetailView.as_view(), name='book_detail'),
    ]

Internal Structure:
    books/views/
    ├── __init__.py      (this file)
    ├── book.py          (Book views)
    ├── category.py      (Category views)
    ├── chapter.py       (Chapter views)
    ├── review.py        (Review views)
    └── tag.py           (Tag views)

Design Decisions:
    - Separate CreateView and UpdateView for clarity and security
    - Consistent naming pattern across all models
    - Permission checks via mixins and manual verification
    - Query optimization to prevent N+1 problems

TODO: Add the following views in future iterations:
    - BookDeleteView           - Soft-delete books
    - BookLikeView             - Toggle like on a book
    - CategoryModerateView     - Approve/reject categories (staff)
    - CategoryDeleteView       - Delete category requests
    - ChapterDeleteView        - Delete chapters
    - ChapterReorderView       - Reorder chapters via drag-and-drop
    - ReviewDeleteView         - Delete reviews
    - ReviewReportView         - Report inappropriate reviews
    - ReviewVoteView           - Mark reviews as helpful/not helpful
    - TagDeleteView            - Delete tags (staff only)
    - TagMergeView             - Merge duplicate tags (staff only)
    - TagAutocompleteView      - AJAX autocomplete for tag input
"""

# ============================================
# Book Views
# ============================================

from .book import (
    BookListView,
    BookDetailView,
    BookCreateView,
    BookUpdateView,
)

# TODO: Import additional book views as they are created
# from .book import (
#     BookDeleteView,
#     BookLikeView,
#     BookPublishView,
#     BookDraftListView,
# )


# ============================================
# Category Views
# ============================================

from .category import (
    CategoryListView,
    CategoryDetailView,
    CategoryCreateView,
    CategoryUpdateView,
)

# TODO: Import additional category views as they are created
# from .category import (
#     CategoryModerateView,
#     CategoryDeleteView,
#     CategoryPendingListView,
# )


# ============================================
# Chapter Views
# ============================================

from .chapter import (
    ChapterListView,
    ChapterDetailView,
    ChapterCreateView,
    ChapterUpdateView,
)

# TODO: Import additional chapter views as they are created
# from .chapter import (
#     ChapterDeleteView,
#     ChapterReorderView,
#     ChapterBulkEditView,
#     ChapterPreviewView,
# )


# ============================================
# Review Views
# ============================================

from .review import (
    ReviewListView,
    ReviewDetailView,
    ReviewCreateView,
    ReviewUpdateView,
)

# TODO: Import additional review views as they are created
# from .review import (
#     ReviewDeleteView,
#     ReviewReportView,
#     ReviewVoteView,
#     ReviewModerateView,
# )


# ============================================
# Tag Views
# ============================================

from .tag import (
    TagListView,
    TagDetailView,
    TagCreateView,
    TagUpdateView,
)

# TODO: Import additional tag views as they are created
# from .tag import (
#     TagDeleteView,
#     TagMergeView,
#     TagAutocompleteView,
#     TagTrendingView,
# )


# ============================================
# Public API Definition
# ============================================

# Define the public API for this package
# Controls what gets imported with: from books.views import *
# Also helps IDEs with autocomplete and static analysis
__all__ = [
    # Book views
    "BookListView",
    "BookDetailView",
    "BookCreateView",
    "BookUpdateView",

    # Category views
    "CategoryListView",
    "CategoryDetailView",
    "CategoryCreateView",
    "CategoryUpdateView",

    # Chapter views
    "ChapterListView",
    "ChapterDetailView",
    "ChapterCreateView",
    "ChapterUpdateView",

    # Review views
    "ReviewListView",
    "ReviewDetailView",
    "ReviewCreateView",
    "ReviewUpdateView",

    # Tag views
    "TagListView",
    "TagDetailView",
    "TagCreateView",
    "TagUpdateView",
]

# TODO: Add additional views to __all__ as they are created
# __all__ = [
#     # Book views
#     "BookListView",
#     "BookDetailView",
#     "BookCreateView",
#     "BookUpdateView",
#     "BookDeleteView",
#     "BookLikeView",
#     
#     # Category views
#     "CategoryListView",
#     "CategoryDetailView",
#     "CategoryCreateView",
#     "CategoryUpdateView",
#     "CategoryModerateView",
#     "CategoryDeleteView",
#     
#     # Chapter views
#     "ChapterListView",
#     "ChapterDetailView",
#     "ChapterCreateView",
#     "ChapterUpdateView",
#     "ChapterDeleteView",
#     "ChapterReorderView",
#     
#     # Review views
#     "ReviewListView",
#     "ReviewDetailView",
#     "ReviewCreateView",
#     "ReviewUpdateView",
#     "ReviewDeleteView",
#     "ReviewReportView",
#     
#     # Tag views
#     "TagListView",
#     "TagDetailView",
#     "TagCreateView",
#     "TagUpdateView",
#     "TagDeleteView",
#     "TagMergeView",
# ]


# ============================================
# View Grouping Utilities (Optional)
# ============================================

# TODO: Add utility constants for grouping related views
# This can be useful for permission checks, URL generation, etc.

# List views (display collections)
# LIST_VIEWS = [
#     BookListView,
#     CategoryListView,
#     ChapterListView,
#     ReviewListView,
#     TagListView,
# ]

# Detail views (display single objects)
# DETAIL_VIEWS = [
#     BookDetailView,
#     CategoryDetailView,
#     ChapterDetailView,
#     ReviewDetailView,
#     TagDetailView,
# ]

# Create views (create new objects)
# CREATE_VIEWS = [
#     BookCreateView,
#     CategoryCreateView,
#     ChapterCreateView,
#     ReviewCreateView,
#     TagCreateView,
# ]

# Update views (edit existing objects)
# UPDATE_VIEWS = [
#     BookUpdateView,
#     CategoryUpdateView,
#     ChapterUpdateView,
#     ReviewUpdateView,
#     TagUpdateView,
# ]

# All CRUD views
# CRUD_VIEWS = LIST_VIEWS + DETAIL_VIEWS + CREATE_VIEWS + UPDATE_VIEWS


# ============================================
# View Permission Utilities (Optional)
# ============================================

# TODO: Add utility functions for permission checking

# def get_views_requiring_authentication():
#     """
#     Get all views that require authentication.
#     
#     Returns:
#         list: View classes that require LoginRequiredMixin
#     
#     Example:
#         auth_views = get_views_requiring_authentication()
#         # [BookCreateView, BookUpdateView, CategoryCreateView, ...]
#     """
#     # TODO: Implement this by checking for LoginRequiredMixin
#     pass


# def get_views_requiring_staff():
#     """
#     Get all views that require staff permission.
#     
#     Returns:
#         list: View classes that require staff permission
#     
#     Example:
#         staff_views = get_views_requiring_staff()
#         # [TagUpdateView, CategoryModerateView, ...]
#     """
#     # TODO: Implement this by checking for UserPassesTestMixin
#     pass


# ============================================
# URL Pattern Helpers (Optional)
# ============================================

# TODO: Add utility functions for URL pattern generation

# def get_url_patterns_for_model(model_name):
#     """
#     Get standard URL patterns for a model.
#     
#     Args:
#         model_name (str): Model name (e.g., 'book', 'category')
#     
#     Returns:
#         list: URL patterns for list, detail, create, update
#     
#     Example:
#         patterns = get_url_patterns_for_model('book')
#         # [
#         #     path('', BookListView.as_view(), name='book_list'),
#         #     path('<slug:slug>/', BookDetailView.as_view(), name='book_detail'),
#         #     path('create/', BookCreateView.as_view(), name='book_create'),
#         #     path('<slug:slug>/edit/', BookUpdateView.as_view(), name='book_edit'),
#         # ]
#     """
#     # TODO: Implement this for consistent URL patterns
#     pass


# ============================================
# View Factory Functions (Optional)
# ============================================

# TODO: Add factory functions for common view patterns

# def get_list_view_config(model, template_prefix, context_object_name):
#     """
#     Create a configured ListView for a model.
#     
#     Args:
#         model: The model class
#         template_prefix (str): Template prefix (e.g., 'books/book')
#         context_object_name (str): Context variable name
#     
#     Returns:
#         ListView: Configured ListView class
#     
#     Example:
#         MyListView = get_list_view_config(Book, 'books/book', 'books')
#     """
#     class ConfiguredListView(ListView):
#         model = model
#         template_name = f'{template_prefix}/list.html'
#         context_object_name = context_object_name
#     
#     return ConfiguredListView


# ============================================
# View Mixins (Optional)
# ============================================

# TODO: Add reusable view mixins

# class AuthorRequiredMixin:
#     """
#     Mixin to ensure only the author can access the view.
#     
#     Usage:
#         class MyView(AuthorRequiredMixin, UpdateView):
#             def get_author_field(self):
#                 return 'author'  # Field name on the model
#     """
#     def dispatch(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         author_field = self.get_author_field()
#         author = getattr(self.object, author_field)
#         
#         if author.user != request.user and not request.user.is_staff:
#             return HttpResponseForbidden(
#                 "You don't have permission to access this resource."
#             )
#         
#         return super().dispatch(request, *args, **kwargs)
#     
#     def get_author_field(self):
#         """Override this to specify the author field name."""
#         raise NotImplementedError


# class QueryOptimizationMixin:
#     """
#     Mixin to add common query optimizations.
#     
#     Automatically adds select_related and prefetch_related
#     based on model relationships.
#     """
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         
#         # TODO: Auto-detect relationships and optimize
#         # This is a simplified example
#         if hasattr(self.model, 'author'):
#             queryset = queryset.select_related('author')
#         
#         return queryset
