"""
URL routing configuration for the books application.

This module defines all URL patterns for books, categories, chapters,
reviews, and tags. It uses slug-based URLs for SEO-friendly paths.

URL Structure:
    /                                    → Book list
    /book/<slug>/                        → Book detail
    /book/create/                        → Create book
    /book/<slug>/edit/                   → Edit book
    /categories/                         → Category list
    /category/<slug>/                    → Category detail
    /category/create/                    → Create category request
    /category/<slug>/edit/               → Edit category request
    /book/<book_slug>/chapters/          → Chapter list
    /book/<book_slug>/chapter/<slug>/    → Chapter detail
    /book/<book_slug>/chapter/create/    → Create chapter
    /book/<book_slug>/chapter/<slug>/edit/ → Edit chapter
    /reviews/                            → Review list
    /review/<id>/                        → Review detail
    /book/<book_slug>/review/create/     → Create review
    /review/<id>/edit/                   → Edit review
    /tags/                               → Tag list
    /tag/<slug>/                         → Tag detail
    /tag/create/                         → Create tag
    /tag/<slug>/edit/                    → Edit tag

Namespace: 'books'
Usage in templates: {% url 'books:book_list' %}
Usage in views: reverse('books:book_detail', kwargs={'slug': book.slug})
"""

from django.urls import path

from books.views import (
    # Book views
    BookListView, BookDetailView, BookCreateView, BookUpdateView,
    # Category views
    CategoryListView, CategoryDetailView, CategoryCreateView, CategoryUpdateView,
    # Chapter views
    ChapterListView, ChapterDetailView, ChapterCreateView, ChapterUpdateView,
    # Review views
    ReviewListView, ReviewDetailView, ReviewCreateView, ReviewUpdateView,
    # Tag views
    TagListView, TagDetailView, TagCreateView, TagUpdateView,
)

# URL namespace for this app
# Allows reversing URLs like: reverse('books:book_detail', kwargs={'slug': 'learning-django'})
app_name = 'books'

urlpatterns = [
    # ============================================
    # 📖 BOOKS
    # ============================================

    # List of all published books
    # URL: /
    # View: BookListView
    # Template: books/book/list.html
    path(
        '',
        BookListView.as_view(),
        name='book_list'
    ),

    # Book detail page with chapters and reviews
    # URL: /book/learning-django/
    # View: BookDetailView
    # Template: books/book/detail.html
    # Parameter: slug - unique URL identifier for the book
    path(
        'book/<slug:slug>/',
        BookDetailView.as_view(),
        name='book_detail'
    ),

    # Create a new book (requires authentication)
    # URL: /book/create/
    # View: BookCreateView
    # Template: books/book/form.html
    # IMPORTANT: This path must be ABOVE book/<slug>/ to avoid "create" being treated as a slug
    path(
        'book/create/',
        BookCreateView.as_view(),
        name='book_create'
    ),

    # Edit an existing book (author only)
    # URL: /book/learning-django/edit/
    # View: BookUpdateView
    # Template: books/book/form.html
    path(
        'book/<slug:slug>/edit/',
        BookUpdateView.as_view(),
        name='book_edit'
    ),

    # ============================================
    # 📁 CATEGORIES
    # ============================================

    # List of all approved categories
    # URL: /categories/
    # View: CategoryListView
    # Template: books/category/list.html
    path(
        'categories/',
        CategoryListView.as_view(),
        name='category_list'
    ),

    # Category detail page with books
    # URL: /category/programming/
    # View: CategoryDetailView
    # Template: books/category/detail.html
    path(
        'category/<slug:slug>/',
        CategoryDetailView.as_view(),
        name='category_detail'
    ),

    # Create a new category request (requires authentication)
    # URL: /category/create/
    # View: CategoryCreateView
    # Template: books/category/form.html
    # New categories start with status=PENDING
    path(
        'category/create/',
        CategoryCreateView.as_view(),
        name='category_create'
    ),

    # Edit a pending category request (author only, only if PENDING)
    # URL: /category/programming/edit/
    # View: CategoryUpdateView
    # Template: books/category/form.html
    path(
        'category/<slug:slug>/edit/',
        CategoryUpdateView.as_view(),
        name='category_edit'
    ),

    # ============================================
    # 📑 CHAPTERS
    # ============================================

    # List of published chapters for a book
    # URL: /book/learning-django/chapters/
    # View: ChapterListView
    # Template: books/chapter/list.html
    # Parameter: book_slug - slug of the parent book
    path(
        'book/<slug:book_slug>/chapters/',
        ChapterListView.as_view(),
        name='chapter_list'
    ),

    # Chapter detail page with rendered Markdown
    # URL: /book/learning-django/chapter/introduction/
    # View: ChapterDetailView
    # Template: books/chapter/detail.html
    # Parameters:
    #   - book_slug: slug of the parent book
    #   - slug: slug of the chapter
    # IMPORTANT: Use different parameter names (book_slug and slug) to avoid conflicts
    path(
        'book/<slug:book_slug>/chapter/<slug:slug>/',
        ChapterDetailView.as_view(),
        name='chapter_detail'
    ),

    # Create a new chapter for a book (book author only)
    # URL: /book/learning-django/chapter/create/
    # View: ChapterCreateView
    # Template: books/chapter/form.html
    # Parameter: book_slug - slug of the parent book
    path(
        'book/<slug:book_slug>/chapter/create/',
        ChapterCreateView.as_view(),
        name='chapter_create'
    ),

    # Edit an existing chapter (book author only)
    # URL: /book/learning-django/chapter/introduction/edit/
    # View: ChapterUpdateView
    # Template: books/chapter/form.html
    # Parameters:
    #   - book_slug: slug of the parent book
    #   - slug: slug of the chapter
    path(
        'book/<slug:book_slug>/chapter/<slug:slug>/edit/',
        ChapterUpdateView.as_view(),
        name='chapter_edit'
    ),

    # ============================================
    # ⭐ REVIEWS
    # ============================================

    # List of all reviews (for moderation/overview)
    # URL: /reviews/
    # View: ReviewListView
    # Template: books/review/list.html
    path(
        'reviews/',
        ReviewListView.as_view(),
        name='review_list'
    ),

    # Review detail page
    # URL: /review/42/
    # View: ReviewDetailView
    # Template: books/review/detail.html
    # Parameter: pk - primary key of the review (reviews use pk, not slug)
    path(
        'review/<int:pk>/',
        ReviewDetailView.as_view(),
        name='review_detail'
    ),

    # Create a new review for a book (requires authentication)
    # URL: /book/learning-django/review/create/
    # View: ReviewCreateView
    # Template: books/review/form.html
    # Parameter: book_slug - slug of the book being reviewed
    # Prevents: self-reviews, duplicate reviews
    path(
        'book/<slug:book_slug>/review/create/',
        ReviewCreateView.as_view(),
        name='review_create'
    ),

    # Edit an existing review (review author only)
    # URL: /review/42/edit/
    # View: ReviewUpdateView
    # Template: books/review/form.html
    # Parameter: pk - primary key of the review
    path(
        'review/<int:pk>/edit/',
        ReviewUpdateView.as_view(),
        name='review_edit'
    ),

    # ============================================
    # 🏷️ TAGS
    # ============================================

    # List of all tags with book counts and tag cloud
    # URL: /tags/
    # View: TagListView
    # Template: books/tag/list.html
    path(
        'tags/',
        TagListView.as_view(),
        name='tag_list'
    ),

    # Tag detail page with books
    # URL: /tag/python/
    # View: TagDetailView
    # Template: books/tag/detail.html
    # Parameter: slug - slug of the tag
    path(
        'tag/<slug:slug>/',
        TagDetailView.as_view(),
        name='tag_detail'
    ),

    # Create a new tag (requires authentication)
    # URL: /tag/create/
    # View: TagCreateView
    # Template: books/tag/form.html
    path(
        'tag/create/',
        TagCreateView.as_view(),
        name='tag_create'
    ),

    # Edit an existing tag (staff only)
    # URL: /tag/python/edit/
    # View: TagUpdateView
    # Template: books/tag/form.html
    path(
        'tag/<slug:slug>/edit/',
        TagUpdateView.as_view(),
        name='tag_edit'
    ),
]