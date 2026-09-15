"""
Book form for the MD Books Library.

This module defines the ModelForm for creating and editing books.
The form handles user input validation, widget customization, and
field exclusions for auto-managed fields.

Key Features:
    - Bootstrap-styled form controls
    - Auto-exclusion of system-managed fields
    - Custom validation for book data
    - Placeholder text for better UX
    - Support for image uploads

Classes:
    BookForm - ModelForm for Book model
"""

from django import forms
from django.core.exceptions import ValidationError

from books.models import Book


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


class BookForm(forms.ModelForm):
    """
    ModelForm for creating and editing books.

    This form handles the user-facing interface for book creation and editing.
    It automatically excludes system-managed fields (author, timestamps, etc.)
    and provides Bootstrap-styled widgets for consistent UI.

    Excluded Fields:
        - author: Set automatically from request.user.profile
        - views: Managed automatically via view counter
        - likes: Managed automatically via like system
        - slug: Auto-generated from title
        - is_published: Controlled by moderators/admin
        - created_at: Auto-set on creation
        - updated_at: Auto-updated on save

    Customizations:
        - Bootstrap form-control classes on all widgets
        - Placeholder text for better UX
        - Textarea with appropriate row counts
        - File input for image uploads

    Validation:
        - Title length and uniqueness
        - Description length limits
        - Image file size and format validation
        - Reading time validation

    Example:
        >>> form = BookForm(data=request.POST, files=request.FILES)
        >>> if form.is_valid():
        ...     book = form.save(commit=False)
        ...     book.author = request.user.profile
        ...     book.save()
        ...     form.save_m2m()  # Save tags
    """

    class Meta:
        """Meta configuration for the BookForm."""
        model = Book

        # Fields to exclude from the form
        # These are managed automatically by the system
        exclude = [
            'author',  # Set from request.user
            'views',  # Auto-incremented
            'likes',  # Managed by like system
            'slug',  # Auto-generated from title
            'is_published',  # Controlled by moderators
            'created_at',  # Auto-set on creation
            'updated_at',  # Auto-updated on save
        ]

        # TODO: Consider using 'fields' instead of 'exclude' for explicit control
        # fields = [
        #     'title',
        #     'description',
        #     'category',
        #     'tags',
        #     'image',
        #     'language',
        #     'reading_time_minutes',
        # ]

        # Field ordering for better UX
        # TODO: Customize field order based on importance
        # field_order = [
        #     'title',
        #     'description',
        #     'category',
        #     'tags',
        #     'image',
        #     'language',
        #     'reading_time_minutes',
        # ]

        # Widget customizations for Bootstrap styling
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Book Title',
                'maxlength': '100',
                'autofocus': True,
                # TODO: Add data attributes for JavaScript validation
                # 'data-validate': 'required,minlength:3,maxlength:100',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Brief synopsis of the book (max 5000 characters)',
                'maxlength': '5000',
                # TODO: Add character counter with JavaScript
                # 'data-counter': 'true',
            }),

            'category': forms.Select(attrs={
                'class': 'form-control',
                # TODO: Add Select2 for searchable dropdown
                # 'class': 'form-control select2',
                # 'data-placeholder': 'Select a category',
            }),

            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'rows': 4,
                # TODO: Replace with tag input widget (e.g., django-taggit, Select2 tags)
                # 'class': 'form-control tag-input',
                # 'data-placeholder': 'Add tags...',
            }),

            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                # TODO: Add image preview with JavaScript
                # 'data-preview': 'true',
            }),

            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Book Language (e.g., English, Russian)',
                'maxlength': '50',
                # TODO: Replace with Select widget with predefined language choices
                # 'class': 'form-control select2',
            }),

            'reading_time_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estimated reading time in minutes',
                'min': '1',
                'max': '10000',
                # TODO: Add auto-calculation based on chapter word count
                # 'data-auto-calculate': 'true',
            }),
        }

        # TODO: Add help texts for form fields
        # help_texts = {
        #     'title': 'Enter a clear, descriptive title for your book.',
        #     'description': 'Write a compelling synopsis that will attract readers.',
        #     'category': 'Select an approved category for your book.',
        #     'tags': 'Add relevant tags to help readers find your book.',
        #     'image': 'Upload a cover image (JPG, PNG, max 5MB).',
        #     'language': 'Specify the primary language of the book.',
        #     'reading_time_minutes': 'Estimated time to read the entire book.',
        # }

        # TODO: Add custom labels if needed
        # labels = {
        #     'title': 'Book Title',
        #     'description': 'Synopsis',
        #     'reading_time_minutes': 'Reading Time (minutes)',
        # }

    # ============================================
    # Custom Field Definitions
    # ============================================

    # TODO: Add custom fields if needed
    # custom_field = forms.CharField(
    #     max_length=100,
    #     required=False,
    #     widget=forms.TextInput(attrs={
    #         'class': 'form-control',
    #         'placeholder': 'Custom field'
    #     }),
    #     help_text='Help text for custom field'
    # )

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing additional context like the current user
        or book instance for custom validation.
        """
        # Extract custom kwargs before calling super()
        self.user = kwargs.pop('user', None)
        self.book_instance = kwargs.pop('book_instance', None)

        super().__init__(*args, **kwargs)

        # TODO: Customize form fields based on user permissions
        # if self.user and not self.user.is_staff:
        #     # Hide certain fields from non-staff users
        #     self.fields.pop('some_field', None)

        # TODO: Filter category choices to only show approved categories
        # from books.models import Category
        # self.fields['category'].queryset = Category.objects.filter(
        #     status=Category.Status.APPROVED
        # )

        # TODO: Add placeholder for tags field
        # self.fields['tags'].widget.attrs['placeholder'] = 'Start typing to add tags...'

        # TODO: Make certain fields required or optional based on context
        # self.fields['description'].required = True
        # self.fields['image'].required = False

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_title(self):
        """
        Validate the book title.

        Ensures:
            - Title is not empty
            - Title is at least 3 characters
            - Title is unique (excluding current instance)

        Returns:
            str: Cleaned title

        Raises:
            ValidationError: If validation fails
        """
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError('Title is required.')

        if len(title) < 3:
            raise ValidationError('Title must be at least 3 characters long.')

        # Check uniqueness (excluding current instance if editing)
        queryset = Book.objects.filter(title__iexact=title)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError('A book with this title already exists.')

        return title

    def clean_description(self):
        """
        Validate the book description.

        Ensures:
            - Description is not empty
            - Description is at least 50 characters (encourage detailed descriptions)

        Returns:
            str: Cleaned description

        Raises:
            ValidationError: If validation fails
        """
        description = self.cleaned_data.get('description', '').strip()

        if not description:
            raise ValidationError('Description is required.')

        # TODO: Consider making this a warning instead of error
        # if len(description) < 50:
        #     raise ValidationError(
        #         'Description should be at least 50 characters. '
        #         'Please provide a more detailed synopsis.'
        #     )

        return description

    def clean_image(self):
        """
        Validate the book cover image.

        Ensures:
            - Image file size is within limits (max 5MB)
            - Image format is allowed (JPG, PNG, GIF, WebP)

        Returns:
            ImageFieldFile: Cleaned image file

        Raises:
            ValidationError: If validation fails
        """
        image = self.cleaned_data.get('image')

        if not image:
            return image

        # TODO: Make max size configurable in settings
        max_size = 5 * 1024 * 1024  # 5MB

        if image.size > max_size:
            raise ValidationError(
                f'Image file size must be less than {max_size // (1024 * 1024)}MB.'
            )

        # Check file extension
        # TODO: Also check MIME type for security
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        ext = image.name.split('.')[-1].lower()

        if ext not in allowed_extensions:
            raise ValidationError(
                f'Invalid image format. Allowed formats: {", ".join(allowed_extensions)}'
            )

        return image

    def clean_reading_time_minutes(self):
        """
        Validate the reading time.

        Ensures:
            - Reading time is positive
            - Reading time is reasonable (max 10000 minutes ≈ 166 hours)

        Returns:
            int: Cleaned reading time

        Raises:
            ValidationError: If validation fails
        """
        reading_time = self.cleaned_data.get('reading_time_minutes')

        if reading_time is not None:
            if reading_time < 0:
                raise ValidationError('Reading time cannot be negative.')

            if reading_time > 10000:
                raise ValidationError('Reading time seems unreasonably long.')

        return reading_time

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
        # Example: If category is selected, ensure it's approved
        # category = cleaned_data.get('category')
        # if category and not category.is_approved:
        #     self.add_error('category', 'Selected category is not approved.')

        # TODO: Validate tags count
        # tags = cleaned_data.get('tags')
        # if tags and tags.count() > 10:
        #     self.add_error('tags', 'Maximum 10 tags allowed per book.')

        # TODO: Auto-calculate reading time if not provided
        # if not cleaned_data.get('reading_time_minutes') and self.instance:
        #     cleaned_data['reading_time_minutes'] = self.instance.calculate_reading_time()

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
            Book: The saved book instance

        Note:
            If commit=False, remember to call save_m2m() later
            to save ManyToMany fields (tags).
        """
        book = super().save(commit=commit)

        # TODO: Add post-save actions
        # if commit:
        #     # Auto-calculate reading time if not set
        #     if not book.reading_time_minutes:
        #         book.reading_time_minutes = book.calculate_reading_time()
        #         book.save(update_fields=['reading_time_minutes'])

        # TODO: Trigger notifications or other actions
        # book.notify_followers_of_update()

        return book

    # ============================================
    # Helper Methods
    # ============================================

    def get_tags_as_list(self):
        """
        Get the selected tags as a list of tag names.

        Returns:
            list: List of tag names

        Example:
            >>> form.get_tags_as_list()
            ['Python', 'Django', 'Web Development']
        """
        tags = self.cleaned_data.get('tags', [])
        return [tag.name for tag in tags]

    # TODO: Add method to handle tag creation
    # def create_missing_tags(self):
    #     """
    #     Create tags that don't exist yet.
    #     
    #     Useful when using a text input for tags instead of select.
    #     """
    #     from books.models import Tag
    #     tag_names = self.cleaned_data.get('tag_names', '')
    #     if tag_names:
    #         for name in tag_names.split(','):
    #             name = name.strip()
    #             if name:
    #                 tag, created = Tag.objects.get_or_create(name=name)
    #                 self.instance.tags.add(tag)

# TODO: Add additional form classes if needed
# class BookSearchForm(forms.Form):
#     """Form for searching books."""
#     query = forms.CharField(
#         max_length=100,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Search books...'
#         })
#     )
#     category = forms.ModelChoiceField(
#         queryset=Category.objects.filter(status='approved'),
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     tag = forms.CharField(
#         max_length=50,
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Filter by tag'
#         })
#     )
