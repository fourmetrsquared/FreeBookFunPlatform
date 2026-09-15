"""
Forms package for the MD Books Library.

This module serves as the public API for all forms in the books application.
It imports and exports all form classes, providing a clean interface for
views and other modules to access forms without knowing the internal structure.

Public API:
    BookForm        - Create/edit books
    CategoryForm    - Create/edit category requests
    ChapterForm     - Create/edit book chapters
    ReviewForm      - Create/edit book reviews
    TagForm         - Create/edit tags

Usage:
    from books.forms import BookForm, ReviewForm

    # In views
    form = BookForm(request.POST, request.FILES)
    if form.is_valid():
        book = form.save(commit=False)
        book.author = request.user.profile
        book.save()

Internal Structure:
    books/forms/
    ├── __init__.py      (this file)
    ├── book.py          (BookForm)
    ├── category.py      (CategoryForm)
    ├── chapter.py       (ChapterForm)
    ├── review.py        (ReviewForm)
    └── tag.py           (TagForm)

TODO: Add additional forms as the application grows:
    - BookSearchForm       (search/filter books)
    - CategorySearchForm   (search/filter categories)
    - ChapterBulkEditForm  (bulk operations on chapters)
    - ReviewModerationForm (moderator actions on reviews)
    - TagMergeForm         (merge duplicate tags)
    - TagBulkForm          (create multiple tags at once)
"""

# Import all form classes from their respective modules
# This allows: from books.forms import BookForm
# Instead of: from books.forms.book import BookForm
from .book import BookForm
from .category import CategoryForm
from .chapter import ChapterForm
from .review import ReviewForm
from .tag import TagForm

# TODO: Import additional forms as they are created
# from .search import BookSearchForm, CategorySearchForm
# from .moderation import ReviewModerationForm, CategoryModerationForm
# from .bulk import ChapterBulkEditForm, TagBulkForm
# from .merge import TagMergeForm

# Define the public API for this package
# Controls what gets imported with: from books.forms import *
# Also helps IDEs with autocomplete and static analysis
__all__ = [
    "BookForm",
    "CategoryForm",
    "ChapterForm",
    "ReviewForm",
    "TagForm",
]

# TODO: Add additional forms to __all__ as they are created
# __all__ = [
#     "BookForm",
#     "CategoryForm",
#     "ChapterForm",
#     "ReviewForm",
#     "TagForm",
#     "BookSearchForm",
#     "CategorySearchForm",
#     "ChapterBulkEditForm",
#     "ReviewModerationForm",
#     "TagMergeForm",
#     "TagBulkForm",
# ]


# ============================================
# Form Factory Functions (Optional)
# ============================================

# TODO: Add factory functions for common form creation patterns
# This can simplify view code and ensure consistent form initialization

# def get_book_form(request, book=None, **kwargs):
#     """
#     Factory function to create a BookForm with common defaults.
#     
#     Args:
#         request: The HTTP request object
#         book: Optional Book instance for editing
#         **kwargs: Additional arguments to pass to the form
#     
#     Returns:
#         BookForm: Initialized form instance
#     
#     Example:
#         # In a view
#         form = get_book_form(request, book=existing_book)
#     """
#     if request.method == 'POST':
#         return BookForm(
#             request.POST,
#             request.FILES,
#             instance=book,
#             user=request.user,
#             **kwargs
#         )
#     else:
#         return BookForm(instance=book, user=request.user, **kwargs)


# def get_chapter_form(request, book, chapter=None, **kwargs):
#     """
#     Factory function to create a ChapterForm with book context.
#     
#     Args:
#         request: The HTTP request object
#         book: The parent Book instance (required)
#         chapter: Optional Chapter instance for editing
#         **kwargs: Additional arguments to pass to the form
#     
#     Returns:
#         ChapterForm: Initialized form instance
#     """
#     if request.method == 'POST':
#         return ChapterForm(
#             request.POST,
#             instance=chapter,
#             book=book,
#             user=request.user,
#             **kwargs
#         )
#     else:
#         return ChapterForm(instance=chapter, book=book, user=request.user, **kwargs)


# def get_review_form(request, book, review=None, **kwargs):
#     """
#     Factory function to create a ReviewForm with book and user context.
#     
#     Args:
#         request: The HTTP request object
#         book: The Book being reviewed (required)
#         review: Optional Review instance for editing
#         **kwargs: Additional arguments to pass to the form
#     
#     Returns:
#         ReviewForm: Initialized form instance
#     """
#     if request.method == 'POST':
#         return ReviewForm(
#             request.POST,
#             instance=review,
#             book=book,
#             user=request.user,
#             **kwargs
#         )
#     else:
#         return ReviewForm(instance=review, book=book, user=request.user, **kwargs)


# ============================================
# Form Validation Utilities (Optional)
# ============================================

# TODO: Add utility functions for common validation patterns

# def validate_image_file(image_file, max_size_mb=5, allowed_extensions=None):
#     """
#     Validate an uploaded image file.
#     
#     Args:
#         image_file: The uploaded file object
#         max_size_mb: Maximum file size in megabytes
#         allowed_extensions: List of allowed file extensions
#     
#     Returns:
#         tuple: (is_valid, error_message)
#     
#     Example:
#         is_valid, error = validate_image_file(request.FILES['image'])
#         if not is_valid:
#             messages.error(request, error)
#     """
#     if allowed_extensions is None:
#         allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
#     
#     if not image_file:
#         return True, None
#     
#     max_size = max_size_mb * 1024 * 1024
#     if image_file.size > max_size:
#         return False, f'Image must be less than {max_size_mb}MB.'
#     
#     ext = image_file.name.split('.')[-1].lower()
#     if ext not in allowed_extensions:
#         return False, f'Invalid format. Allowed: {", ".join(allowed_extensions)}'
#     
#     return True, None


# def validate_markdown_content(content, min_words=50):
#     """
#     Validate Markdown content for chapters.
#     
#     Args:
#         content: The Markdown content string
#         min_words: Minimum word count
#     
#     Returns:
#         tuple: (is_valid, error_message, word_count)
#     
#     Example:
#         is_valid, error, word_count = validate_markdown_content(chapter.content)
#         if not is_valid:
#             messages.error(request, error)
#     """
#     if not content or not content.strip():
#         return False, 'Content cannot be empty.', 0
#     
#     word_count = len(content.split())
#     if word_count < min_words:
#         return False, f'Content must be at least {min_words} words.', word_count
#     
#     # Check for unclosed code blocks
#     if content.count('```') % 2 != 0:
#         return False, 'Unclosed code block detected.', word_count
#     
#     return True, None, word_count


# ============================================
# Form Rendering Utilities (Optional)
# ============================================

# TODO: Add utility functions for form rendering in templates

# def get_form_errors_as_list(form):
#     """
#     Get all form errors as a flat list of strings.
#     
#     Useful for displaying all errors in a single alert box.
#     
#     Args:
#         form: The form instance
#     
#     Returns:
#         list: List of error messages
#     
#     Example:
#         errors = get_form_errors_as_list(form)
#         # ['Title is required.', 'Image must be less than 5MB.']
#     """
#     errors = []
#     
#     # Field errors
#     for field, field_errors in form.errors.items():
#         for error in field_errors:
#             if field == '__all__':
#                 errors.append(error)
#             else:
#                 errors.append(f'{field}: {error}')
#     
#     return errors


# def get_form_field_order(form, custom_order=None):
#     """
#     Get form fields in a custom order for template rendering.
#     
#     Args:
#         form: The form instance
#         custom_order: List of field names in desired order
#     
#     Returns:
#         list: List of BoundField objects in order
#     
#     Example:
#         fields = get_form_field_order(form, ['title', 'description', 'image'])
#         {% for field in fields %}
#             {{ field }}
#         {% endfor %}
#     """
#     if custom_order is None:
#         return list(form)
#     
#     fields = []
#     for field_name in custom_order:
#         if field_name in form.fields:
#             fields.append(form[field_name])
#     
#     # Add any remaining fields not in custom_order
#     for field_name in form.fields:
#         if field_name not in custom_order:
#             fields.append(form[field_name])
#     
#     return fields
