"""
Models package for the MD Books Library.

This module serves as the public API for all models in the books application.
It imports and exports all model classes, providing a clean interface for
views, forms, admin, and other modules to access models without knowing
the internal file structure.

Public API:
    Category    - Book categories with request-approval workflow
    Tag         - Flexible keyword-based book classification
    Book        - Main book entity with metadata and relationships
    Chapter     - Book chapters containing Markdown content
    Review      - User reviews and ratings for books

Model Relationships:
    Profile (from accounts app)
        │
        ├──< Book (author) ─────────────────┐
        │       │                           │
        │       ├──< Chapter (book)         │
        │       ├──< Review (book, author)  │
        │       ├──> Category (FK)          │
        │       └──<> Tag (M2M)             │
        │                                   │
        └──< Category (author of request) ──┘

Import Order (IMPORTANT):
    The import order matters because of ForeignKey dependencies:
    1. Category (no dependencies on other books models)
    2. Tag (no dependencies on other books models)
    3. Book (depends on Category, Tag, Profile)
    4. Chapter (depends on Book)
    5. Review (depends on Book, Profile)

    Django requires models to be imported in dependency order to avoid
    circular import errors during app initialization.

Usage:
    # In views, forms, admin, etc.
    from books.models import Book, Category, Tag

    book = Book.objects.get(slug='learning-django')
    categories = Category.get_approved_categories()

Internal Structure:
    books/models/
    ├── __init__.py      (this file)
    ├── category.py      (Category model)
    ├── tag.py           (Tag model)
    ├── book.py          (Book model)
    ├── chapter.py       (Chapter model)
    └── review.py        (Review model)

Django Model Discovery:
    Django automatically discovers models by importing the 'models' module
    of each installed app. This __init__.py ensures all models are properly
    registered with Django's ORM and appear in migrations.
"""

# ============================================
# Model Imports (ORDER MATTERS!)
# ============================================

# Import order follows dependency graph:
# Models with no internal dependencies first,
# then models that depend on them.

# 3. Book - depends on Category (FK) and Tag (M2M)
from .book import Book
# 1. Category - independent model (only depends on Profile from accounts)
from .category import Category
# 4. Chapter - depends on Book (FK)
from .chapter import Chapter
# 5. Review - depends on Book (FK) and Profile (FK)
from .review import Review
# 2. Tag - independent model (no internal dependencies)
from .tag import Tag

# TODO: Import additional models as they are created
# from .bookmark import Bookmark              # User bookmarks for books
# from .reading_progress import ReadingProgress  # Track reading progress
# from .like import BookLike                  # Track individual likes
# from .view import BookView                  # Track individual views
# from .review_flag import ReviewFlag         # Flagged reviews for moderation
# from .review_vote import ReviewVote         # Helpful/not helpful votes
# from .category_audit_log import CategoryAuditLog  # Audit trail for categories
# from .tag_synonym import TagSynonym         # Tag synonym mappings


# ============================================
# Public API Definition
# ============================================

# Define the public API for this package
# Controls what gets imported with: from books.models import *
# Also helps IDEs with autocomplete and static analysis
__all__ = [
    'Category',
    'Tag',
    'Book',
    'Chapter',
    'Review',
]

# TODO: Add additional models to __all__ as they are created
# __all__ = [
#     'Category',
#     'Tag',
#     'Book',
#     'Chapter',
#     'Review',
#     'Bookmark',
#     'ReadingProgress',
#     'BookLike',
#     'BookView',
#     'ReviewFlag',
#     'ReviewVote',
#     'CategoryAuditLog',
#     'TagSynonym',
# ]


# ============================================
# Model Grouping Utilities (Optional)
# ============================================

# TODO: Add utility constants for grouping related models
# This can be useful for admin registration, permissions, etc.

# Content models (main entities in the library)
# CONTENT_MODELS = [Book, Chapter]

# Classification models (organize content)
# CLASSIFICATION_MODELS = [Category, Tag]

# Interaction models (user engagement)
# INTERACTION_MODELS = [Review, Bookmark, ReadingProgress, BookLike, BookView]

# Moderation models (content governance)
# MODERATION_MODELS = [ReviewFlag, CategoryAuditLog]

# ALL_MODELS = (
#     CONTENT_MODELS +
#     CLASSIFICATION_MODELS +
#     INTERACTION_MODELS +
#     MODERATION_MODELS
# )


# ============================================
# Model Managers (Optional)
# ============================================

# TODO: Consider creating custom managers for common queries
# These can be exposed here for convenient access

# Example:
# class PublishedBooksManager(models.Manager):
#     """Manager for published books only."""
#     def get_queryset(self):
#         return super().get_queryset().filter(is_published=True)

# Then in Book model:
#     published = PublishedBooksManager()

# Usage:
# Book.published.all()  # Returns only published books


# ============================================
# Query Optimization Helpers (Optional)
# ============================================

# TODO: Add helper functions for common optimized queries
# These prevent N+1 query problems in views

# def get_books_with_related_data():
#     """
#     Get books with all related data pre-fetched.
#
#     Optimized for list views displaying book cards.
#     Uses select_related for FK and prefetch_related for M2M.
#
#     Returns:
#         QuerySet: Optimized queryset of books
#
#     Example:
#         books = get_books_with_related_data()
#         for book in books:
#             print(book.author.name)  # No additional query
#             print(book.tags.all())    # No additional query
#     """
#     return Book.objects.select_related(
#         'author', 'category'
#     ).prefetch_related(
#         'tags'
#     ).annotate(
#         review_count=Count('reviews'),
#         avg_rating=Avg('reviews__rating'),
#         chapter_count=Count('chapters', filter=Q(chapters__is_published=True))
#     )


# def get_book_with_all_details(slug):
#     """
#     Get a single book with all related data for detail view.
#
#     Args:
#         slug (str): Book slug
#
#     Returns:
#         Book: Book instance with all related data
#
#     Example:
#         book = get_book_with_all_details('learning-django')
#     """
#     return Book.objects.select_related(
#         'author', 'category'
#     ).prefetch_related(
#         'tags',
#         Prefetch(
#             'chapters',
#             queryset=Chapter.objects.filter(is_published=True).order_by('order')
#         ),
#         Prefetch(
#             'reviews',
#             queryset=Review.objects.select_related('author').order_by('-created_at')
#         )
#     ).get(slug=slug)


# ============================================
# Model Signals (Optional)
# ============================================

# TODO: Import signal handlers if defined in separate module
# from . import signals

# Or define signals here:
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
#
# @receiver(post_save, sender=Book)
# def book_saved_handler(sender, instance, created, **kwargs):
#     """Handle book save events."""
#     if created:
#         # Notify followers, update search index, etc.
#         pass
#
# @receiver(post_delete, sender=Book)
# def book_deleted_handler(sender, instance, **kwargs):
#     """Handle book deletion events."""
#     # Clean up related data, update search index, etc.
#     pass


# ============================================
# Abstract Base Classes (Optional)
# ============================================

# TODO: Consider creating abstract base models for common fields
# This promotes code reuse and consistency

# class TimestampedModel(models.Model):
#     """Abstract base model with created_at and updated_at fields."""
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         abstract = True

# class SlugModel(models.Model):
#     """Abstract base model with auto-generated slug."""
#     slug = models.SlugField(max_length=100, unique=True, blank=True)
#
#     class Meta:
#         abstract = True
#
#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(getattr(self, 'title', '') or getattr(self, 'name', ''))
#         super().save(*args, **kwargs)

# class AuthorTrackingModel(models.Model):
#     """Abstract base model with author tracking."""
#     author = models.ForeignKey(
#         'accounts.Profile',
#         on_delete=models.CASCADE,
#         related_name='%(class)s_items'
#     )
#
#     class Meta:
#         abstract = True


# ============================================
# Model Documentation Helpers (Optional)
# ============================================

# TODO: Add helper functions for model documentation

# def get_model_relationships():
#     """
#     Get a dictionary describing all model relationships.
#
#     Useful for generating documentation or diagrams.
#
#     Returns:
#         dict: Model relationships
#
#     Example:
#         relationships = get_model_relationships()
#         # {
#         #     'Book': {
#         #         'author': {'type': 'ForeignKey', 'to': 'Profile'},
#         #         'category': {'type': 'ForeignKey', 'to': 'Category'},
#         #         'tags': {'type': 'ManyToManyField', 'to': 'Tag'},
#         #         'chapters': {'type': 'ReverseForeignKey', 'from': 'Chapter'},
#         #         'reviews': {'type': 'ReverseForeignKey', 'from': 'Review'},
#         #     },
#         #     ...
#         # }
#     """
#     relationships = {}
#
#     for model in [Category, Tag, Book, Chapter, Review]:
#         model_name = model.__name__
#         relationships[model_name] = {}
#
#         # Forward relationships
#         for field in model._meta.get_fields():
#             if field.is_relation:
#                 if field.many_to_one:
#                     relationships[model_name][field.name] = {
#                         'type': 'ForeignKey',
#                         'to': field.related_model.__name__
#                     }
#                 elif field.one_to_many:
#                     relationships[model_name][field.name] = {
#                         'type': 'ReverseForeignKey',
#                         'from': field.related_model.__name__
#                     }
#                 elif field.many_to_many:
#                     relationships[model_name][field.name] = {
#                         'type': 'ManyToManyField',
#                         'to': field.related_model.__name__
#                     }
#
#     return relationships


# def get_model_field_names(model_class):
#     """
#     Get all field names for a model.
#
#     Args:
#         model_class: The model class
#
#     Returns:
#         list: Field names
#
#     Example:
#         fields = get_model_field_names(Book)
#         # ['id', 'title', 'slug', 'description', ...]
#     """
#     return [field.name for field in model_class._meta.get_fields()]
