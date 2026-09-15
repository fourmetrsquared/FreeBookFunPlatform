"""
Chapter form for the MD Books Library.

This module defines the ModelForm for creating and editing book chapters.
Chapters contain Markdown-formatted content and are the primary content units
in the library.

Key Features:
    - Bootstrap-styled form controls
    - Markdown editor support with preview
    - Auto-exclusion of system-managed fields
    - Custom validation for chapter data
    - Word count and reading time calculation
    - Duplicate chapter title prevention within book
    - Order uniqueness validation

Classes:
    ChapterForm - ModelForm for Chapter model
"""

from django import forms
from django.core.exceptions import ValidationError

from books.models import Chapter


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


class ChapterForm(forms.ModelForm):
    """
    ModelForm for creating and editing book chapters.

    This form handles the user-facing interface for chapter creation and editing.
    It automatically excludes system-managed fields (book, slug, timestamps)
    and provides Bootstrap-styled widgets with Markdown editor support.

    Excluded Fields:
        - book: Set automatically from URL parameter in the view
        - slug: Auto-generated from title
        - is_published: Controlled by author/moderators
        - created_at: Auto-set on creation
        - updated_at: Auto-updated on save

    Customizations:
        - Bootstrap form-control classes on all widgets
        - Markdown editor class for content field
        - Placeholder text for better UX
        - Textarea with appropriate row counts
        - Number input with min/max constraints

    Validation:
        - Title length and uniqueness within book
        - Content minimum length (encourage quality)
        - Order uniqueness within book
        - Word count calculation

    Example:
        >>> form = ChapterForm(data=request.POST)
        >>> if form.is_valid():
        ...     chapter = form.save(commit=False)
        ...     chapter.book = book  # Set from URL parameter
        ...     chapter.save()
    """

    class Meta:
        """Meta configuration for the ChapterForm."""
        model = Chapter

        # Fields to exclude from the form
        # These are managed automatically by the system
        exclude = [
            'book',  # Set from URL parameter in view
            'slug',  # Auto-generated from title
            'is_published',  # Controlled by author/moderators
            'created_at',  # Auto-set on creation
            'updated_at',  # Auto-updated on save
        ]

        # TODO: Consider using 'fields' instead of 'exclude' for explicit control
        # fields = ['title', 'description', 'content', 'order']

        # TODO: Customize field order based on importance
        # field_order = ['title', 'content', 'description', 'order']

        # Widget customizations for Bootstrap styling and Markdown support
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Chapter Title',
                'maxlength': '100',
                'autofocus': True,
                # TODO: Add data attributes for JavaScript validation
                # 'data-validate': 'required,minlength:3,maxlength:100',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief summary of this chapter (optional, max 1000 characters)',
                'maxlength': '1000',
                # TODO: Add character counter with JavaScript
                # 'data-counter': 'true',
            }),

            'content': forms.Textarea(attrs={
                'class': 'form-control markdown-editor',
                'rows': 20,
                'placeholder': 'Write your chapter content in Markdown format...\n\n'
                               '# Chapter Title\n\n'
                               'Your content here...\n\n'
                               '## Section 1\n\n'
                               'More content...',
                # TODO: Add Markdown preview toggle button
                # 'data-preview-toggle': 'true',
                # TODO: Add real-time word count display
                # 'data-word-count': 'true',
                # TODO: Add syntax highlighting support
                # 'data-syntax-highlight': 'true',
            }),

            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Chapter order (1, 2, 3, ...)',
                'min': '1',
                'max': '1000',
                # TODO: Add auto-increment suggestion
                # 'data-auto-increment': 'true',
            }),
        }

        # TODO: Add help texts for form fields
        # help_texts = {
        #     'title': 'A clear, descriptive title for this chapter.',
        #     'description': 'Optional brief summary to help readers understand what this chapter covers.',
        #     'content': 'Write your chapter content using Markdown syntax. '
        #                'Use # for headings, ** for bold, * for italic, etc.',
        #     'order': 'The position of this chapter in the book. '
        #              'Chapters are displayed in order from lowest to highest.',
        # }

        # TODO: Add custom labels if needed
        # labels = {
        #     'title': 'Chapter Title',
        #     'description': 'Chapter Summary (optional)',
        #     'content': 'Chapter Content (Markdown)',
        #     'order': 'Chapter Number',
        # }

    # ============================================
    # Custom Field Definitions
    # ============================================

    # TODO: Add custom fields if needed
    # auto_calculate_reading_time = forms.BooleanField(
    #     required=False,
    #     initial=True,
    #     widget=forms.CheckboxInput(attrs={
    #         'class': 'form-check-input',
    #     }),
    #     help_text='Automatically calculate reading time based on word count'
    # )

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing additional context like the parent book instance
        for custom validation and order suggestions.

        Custom kwargs:
            book (Book): The parent book instance
            user (User): The currently authenticated user
        """
        # Extract custom kwargs before calling super()
        self.book = kwargs.pop('book', None)
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # TODO: Set initial order value if creating a new chapter
        # if not self.instance.pk and self.book:
        #     max_order = Chapter.objects.filter(book=self.book).aggregate(
        #         models.Max('order')
        #     )['order__max'] or 0
        #     self.fields['order'].initial = max_order + 1

        # TODO: Add Markdown toolbar with formatting buttons
        # self.fields['content'].widget.attrs['data-toolbar'] = 'true'

        # TODO: Add live preview panel
        # self.fields['content'].widget.attrs['data-live-preview'] = 'true'

        # TODO: Customize form based on user permissions
        # if self.user and not self.user.is_staff:
        #     # Hide certain fields from non-staff users
        #     pass

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_title(self):
        """
        Validate the chapter title.

        Ensures:
            - Title is not empty
            - Title is at least 3 characters
            - Title is unique within the parent book

        Returns:
            str: Cleaned title

        Raises:
            ValidationError: If validation fails
        """
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError('Chapter title is required.')

        if len(title) < 3:
            raise ValidationError('Chapter title must be at least 3 characters long.')

        # Check uniqueness within the book
        if self.book:
            queryset = Chapter.objects.filter(book=self.book, title__iexact=title)

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A chapter with the title "{title}" already exists in this book. '
                    'Please choose a different title.'
                )

        # TODO: Add profanity/inappropriate content filter
        # if contains_inappropriate_words(title):
        #     raise ValidationError('Chapter title contains inappropriate language.')

        return title

    def clean_description(self):
        """
        Validate the chapter description.

        Description is optional, but if provided, should be meaningful.

        Returns:
            str: Cleaned description
        """
        description = self.cleaned_data.get('description', '').strip()

        # TODO: Add minimum length validation if description is provided
        # if description and len(description) < 10:
        #     raise ValidationError(
        #         'Description should be at least 10 characters if provided.'
        #     )

        return description

    def clean_content(self):
        """
        Validate the chapter content.

        Ensures:
            - Content is not empty
            - Content has minimum word count (encourage quality)
            - Content is valid Markdown (basic check)

        Returns:
            str: Cleaned content

        Raises:
            ValidationError: If validation fails
        """
        content = self.cleaned_data.get('content', '').strip()

        if not content:
            raise ValidationError('Chapter content cannot be empty.')

        # Calculate word count
        word_count = len(content.split())

        # TODO: Make minimum word count configurable in settings
        min_words = 50
        if word_count < min_words:
            raise ValidationError(
                f'Chapter content must be at least {min_words} words. '
                f'Your content has {word_count} words.'
            )

        # TODO: Validate Markdown syntax (basic check)
        # Check for common Markdown errors
        # if content.count('```') % 2 != 0:
        #     raise ValidationError(
        #         'Unclosed code block detected. Please check your Markdown syntax.'
        #     )

        # TODO: Check for broken links or images
        # import re
        # broken_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        # for text, url in broken_links:
        #     if not url.startswith(('http://', 'https://', '/')):
        #         raise ValidationError(
        #             f'Invalid link URL: {url}. Links must be absolute or root-relative.'
        #         )

        # TODO: Add content quality checks
        # - Check for repeated characters (e.g., "aaaa...")
        # - Check for placeholder text (e.g., "Lorem ipsum")
        # - Check for TODO/FIXME markers

        return content

    def clean_order(self):
        """
        Validate the chapter order.

        Ensures:
            - Order is positive
            - Order is unique within the parent book

        Returns:
            int: Cleaned order

        Raises:
            ValidationError: If validation fails
        """
        order = self.cleaned_data.get('order')

        if order is None:
            # TODO: Auto-assign next available order if not provided
            # if self.book:
            #     max_order = Chapter.objects.filter(book=self.book).aggregate(
            #         models.Max('order')
            #     )['order__max'] or 0
            #     return max_order + 1
            raise ValidationError('Chapter order is required.')

        if order < 1:
            raise ValidationError('Chapter order must be at least 1.')

        # Check order uniqueness within the book
        if self.book:
            queryset = Chapter.objects.filter(book=self.book, order=order)

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise ValidationError(
                    f'A chapter with order {order} already exists in this book. '
                    'Please choose a different order number.'
                )

        return order

    # ============================================
    # Form-Level Validation
    # ============================================

    def clean(self):
        """
        Perform form-level validation.

        Validates relationships between fields and ensures
        overall form consistency.

        Returns:
            dict: Cleaned data

        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()

        # TODO: Add cross-field validation
        # Example: Warn if title is too similar to description
        # title = cleaned_data.get('title', '')
        # description = cleaned_data.get('description', '')
        # if title and description and title.lower() in description.lower():
        #     self.add_error(
        #         'description',
        #         'Description should not repeat the chapter title.'
        #     )

        # TODO: Validate content length vs. reading time
        # content = cleaned_data.get('content', '')
        # word_count = len(content.split())
        # if word_count > 50000:  # Very long chapter
        #     self.add_error(
        #         'content',
        #         'This chapter is very long. Consider splitting it into multiple chapters.'
        #     )

        # TODO: Check for duplicate content (plagiarism detection)
        # This would require comparing with other chapters in the book

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
            Chapter: The saved chapter instance

        Note:
            The book should be set by the view before calling save(),
            or use save(commit=False) and set it manually.
        """
        chapter = super().save(commit=commit)

        # TODO: Add post-save actions
        # if commit:
        #     # Update parent book's reading time
        #     chapter.book.reading_time_minutes = chapter.book.calculate_reading_time()
        #     chapter.book.save(update_fields=['reading_time_minutes'])

        # TODO: Reorder other chapters if necessary
        # self._reorder_chapters(chapter)

        # TODO: Clear cached chapter data
        # from django.core.cache import cache
        # cache.delete(f'book_{chapter.book.id}_chapters')

        return chapter

    # ============================================
    # Helper Methods
    # ============================================

    def get_word_count(self):
        """
        Get the word count of the chapter content.

        Returns:
            int: Number of words in the content

        Example:
            >>> form.get_word_count()
            2500
        """
        content = self.cleaned_data.get('content', '')
        return len(content.split()) if content else 0

    def get_reading_time_minutes(self):
        """
        Estimate reading time based on word count.

        Average reading speed: 225 words per minute.

        Returns:
            int: Estimated reading time in minutes

        Example:
            >>> form.get_reading_time_minutes()
            11
        """
        word_count = self.get_word_count()
        return max(1, word_count // 225)

    def get_next_available_order(self):
        """
        Get the next available order number for a new chapter.

        Returns:
            int: Next available order number

        Example:
            >>> form.get_next_available_order()
            5
        """
        if not self.book:
            return 1

        max_order = Chapter.objects.filter(book=self.book).aggregate(
            models.Max('order')
        )['order__max'] or 0

        return max_order + 1

    def get_existing_orders(self):
        """
        Get list of existing order numbers in the book.

        Useful for displaying available order numbers to users.

        Returns:
            list: List of existing order numbers

        Example:
            >>> form.get_existing_orders()
            [1, 2, 3, 5, 7]
        """
        if not self.book:
            return []

        return list(
            Chapter.objects.filter(book=self.book)
            .values_list('order', flat=True)
            .order_by('order')
        )

    # TODO: Add method to handle chapter reordering
    # def reorder_chapters(self, new_order):
    #     """
    #     Reorder chapters in the book.
    #     
    #     Args:
    #         new_order (list): List of chapter IDs in desired order
    #     """
    #     if not self.book:
    #         return
    #     
    #     for index, chapter_id in enumerate(new_order, start=1):
    #         Chapter.objects.filter(
    #             book=self.book,
    #             pk=chapter_id
    #         ).update(order=index)

# ============================================
# Additional Form Classes
# ============================================

# TODO: Add form for bulk chapter operations
# class ChapterBulkEditForm(forms.Form):
#     """Form for bulk editing multiple chapters."""
#     chapters = forms.ModelMultipleChoiceField(
#         queryset=Chapter.objects.all(),
#         widget=forms.CheckboxSelectMultiple(attrs={
#             'class': 'form-check-input',
#         })
#     )
#     action = forms.ChoiceField(
#         choices=[
#             ('publish', 'Publish'),
#             ('unpublish', 'Unpublish'),
#             ('delete', 'Delete'),
#         ],
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     
#     def __init__(self, *args, **kwargs):
#         book = kwargs.pop('book', None)
#         super().__init__(*args, **kwargs)
#         if book:
#             self.fields['chapters'].queryset = Chapter.objects.filter(book=book)


# TODO: Add form for chapter reordering
# class ChapterReorderForm(forms.Form):
#     """Form for reordering chapters via drag-and-drop."""
#     chapter_ids = forms.CharField(
#         widget=forms.HiddenInput(),
#         help_text='Comma-separated list of chapter IDs in desired order'
#     )
#     
#     def clean_chapter_ids(self):
#         ids_str = self.cleaned_data.get('chapter_ids', '')
#         try:
#             ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
#             return ids
#         except ValueError:
#             raise ValidationError('Invalid chapter IDs format.')


# TODO: Add form for Markdown preview
# class ChapterPreviewForm(forms.Form):
#     """Form for previewing Markdown content."""
#     content = forms.CharField(
#         widget=forms.Textarea(attrs={
#             'class': 'form-control',
#             'rows': 20,
#         })
#     )
#     
#     def get_rendered_html(self):
#         """
#         Render the Markdown content to HTML.
#         
#         Returns:
#             str: HTML-rendered content
#         """
#         import markdown
#         content = self.cleaned_data.get('content', '')
#         return markdown.markdown(
#             content,
#             extensions=['fenced_code', 'tables', 'toc', 'codehilite']
#         )
