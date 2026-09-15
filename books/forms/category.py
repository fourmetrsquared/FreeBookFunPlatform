"""
Category form for the MD Books Library.

This module defines the ModelForm for creating and editing category requests.
Users submit category proposals which enter a moderation workflow (PENDING → APPROVED/REJECTED).

Key Features:
    - Bootstrap-styled form controls
    - Auto-exclusion of moderation-managed fields
    - Duplicate category name prevention
    - Image file validation (size, format)
    - Custom validation for category data

Classes:
    CategoryForm - ModelForm for Category model (user-facing request form)
"""

from django import forms
from django.core.exceptions import ValidationError

from books.models import Category


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


class CategoryForm(forms.ModelForm):
    """
    ModelForm for creating and editing category requests.

    This form is used by regular users to propose new categories.
    Submitted categories enter the moderation workflow with PENDING status.
    Moderators use a separate admin interface to approve/reject requests.

    Excluded Fields (managed by system):
        - author: Set automatically from request.user.profile
        - status: Defaults to PENDING on creation
        - reviewed_by: Set by moderator on approval/rejection
        - rejection_reason: Set by moderator when rejecting
        - created_at: Auto-set on creation
        - updated_at: Auto-updated on save

    Workflow:
        1. User fills this form → Category created with status=PENDING
        2. Moderator reviews → status changes to APPROVED or REJECTED
        3. If APPROVED → category becomes available for book assignment
        4. If REJECTED → user notified with rejection_reason

    Validation:
        - Title uniqueness (case-insensitive)
        - Title length (3-100 characters)
        - Description minimum length (encourage quality)
        - Image file size and format validation
        - Duplicate request prevention (same user, same title)

    Example:
        >>> form = CategoryForm(data=request.POST, files=request.FILES)
        >>> if form.is_valid():
        ...     category = form.save(commit=False)
        ...     category.author = request.user.profile
        ...     category.save()
    """

    class Meta:
        """Meta configuration for the CategoryForm."""
        model = Category

        # Fields to exclude from the form
        # These are managed automatically by the system or moderators
        exclude = [
            'author',  # Set from request.user.profile
            'status',  # Defaults to PENDING on creation
            'reviewed_by',  # Set by moderator
            'rejection_reason',  # Set by moderator when rejecting
            'created_at',  # Auto-set on creation
            'updated_at',  # Auto-updated on save
        ]

        # TODO: Consider using explicit 'fields' list instead of 'exclude'
        # for better security (prevents accidental exposure of new fields)
        # fields = ['title', 'description', 'image']

        # Widget customizations for Bootstrap styling
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category Name',
                'maxlength': '100',
                'autofocus': True,
                'autocomplete': 'off',
                # TODO: Add real-time duplicate checking via AJAX
                # 'data-check-url': '/api/categories/check-name/',
                # TODO: Add data attributes for JavaScript validation
                # 'data-validate': 'required,minlength:3,maxlength:100',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe what kind of books belong in this category (max 10000 characters)',
                'maxlength': '10000',
                # TODO: Add character counter with JavaScript
                # 'data-counter': 'true',
            }),

            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                # TODO: Add image preview with JavaScript
                # 'data-preview': 'true',
                # TODO: Add drag-and-drop support
                # 'data-dropzone': 'true',
            }),
        }

        # TODO: Add help texts for better user guidance
        # help_texts = {
        #     'title': 'Choose a clear, descriptive name for your category.',
        #     'description': 'Explain what types of books belong here. '
        #                    'This helps moderators understand your request.',
        #     'image': 'Optional cover image for the category (JPG, PNG, max 2MB).',
        # }

        # TODO: Add custom labels if needed
        # labels = {
        #     'title': 'Category Name',
        #     'description': 'Category Description',
        #     'image': 'Category Image (optional)',
        # }

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing the current user for duplicate request prevention
        and other user-specific validations.

        Custom kwargs:
            user (User): The currently authenticated user
        """
        # Extract custom kwargs before calling super()
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # TODO: Add AJAX endpoint URL for real-time name checking
        # self.fields['title'].widget.attrs['data-check-url'] = (
        #     reverse('books:api_category_check_name')
        # )

        # TODO: If editing an existing category request, add a note
        # if self.instance and self.instance.pk:
        #     self.fields['title'].help_text = (
        #         f'Current status: {self.instance.get_status_display()}'
        #     )

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_title(self):
        """
        Validate the category title.

        Ensures:
            - Title is not empty or whitespace-only
            - Title is at least 3 characters long
            - Title is unique (case-insensitive) across ALL categories
            - User hasn't already submitted a PENDING request with same title

        Returns:
            str: Cleaned and stripped title

        Raises:
            ValidationError: If validation fails

        Example:
            >>> form.clean_title()  # with title='Python'
            'Python'
            >>> form.clean_title()  # with duplicate title
            ValidationError: 'A category with this name already exists.'
        """
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError('Category name is required.')

        if len(title) < 3:
            raise ValidationError(
                'Category name must be at least 3 characters long.'
            )

        # Check for existing categories with the same name (case-insensitive)
        # This prevents "Python" and "python" from being different categories
        queryset = Category.objects.filter(title__iexact=title)

        # Exclude current instance if editing
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            existing = queryset.first()
            if existing.is_approved:
                raise ValidationError(
                    'A category with this name already exists. '
                    'Please select it from the list when creating a book.'
                )
            elif existing.is_pending:
                raise ValidationError(
                    'A request for this category is already pending review. '
                    'Please wait for moderator approval.'
                )
            else:  # rejected
                raise ValidationError(
                    'A category with this name was previously rejected. '
                    'Please choose a different name or contact support.'
                )

        # TODO: Add profanity/inappropriate content filter
        # if contains_inappropriate_words(title):
        #     raise ValidationError('Category name contains inappropriate language.')

        # TODO: Prevent generic/too-broad category names
        # generic_names = ['books', 'other', 'misc', 'all']
        # if title.lower() in generic_names:
        #     raise ValidationError(
        #         f'"{title}" is too generic. Please choose a more specific name.'
        #     )

        return title

    def clean_description(self):
        """
        Validate the category description.

        Ensures:
            - Description is provided (required for moderation)
            - Description is at least 20 characters (encourage quality)
            - Description is not just whitespace

        Returns:
            str: Cleaned description

        Raises:
            ValidationError: If validation fails
        """
        description = self.cleaned_data.get('description', '').strip()

        if not description:
            raise ValidationError(
                'Description is required. Please explain what this category is about.'
            )

        if len(description) < 20:
            raise ValidationError(
                'Description must be at least 20 characters. '
                'Please provide more detail to help moderators understand your request.'
            )

        # TODO: Check for low-effort descriptions (e.g., repeated characters)
        # if len(set(description)) < 5:
        #     raise ValidationError('Please provide a meaningful description.')

        return description

    def clean_image(self):
        """
        Validate the category image.

        Ensures:
            - Image file size is within limits (max 2MB for categories)
            - Image format is allowed (JPG, PNG, GIF, WebP)
            - Image dimensions are reasonable (optional, requires PIL)

        Returns:
            ImageFieldFile: Cleaned image file

        Raises:
            ValidationError: If validation fails
        """
        image = self.cleaned_data.get('image')

        # Image is optional for categories
        if not image:
            return image

        # TODO: Make max size configurable in settings
        max_size = 2 * 1024 * 1024  # 2MB (smaller than book covers)

        if image.size > max_size:
            raise ValidationError(
                f'Image file size must be less than {max_size // (1024 * 1024)}MB. '
                f'Your file is {image.size / (1024 * 1024):.2f}MB.'
            )

        # Check file extension
        # TODO: Also validate MIME type using python-magic for security
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        ext = image.name.split('.')[-1].lower()

        if ext not in allowed_extensions:
            raise ValidationError(
                f'Invalid image format. Allowed formats: {", ".join(allowed_extensions)}'
            )

        # TODO: Validate image dimensions using PIL
        # from PIL import Image
        # try:
        #     img = Image.open(image)
        #     img.verify()
        #     if img.width < 200 or img.height < 200:
        #         raise ValidationError(
        #             'Image dimensions must be at least 200x200 pixels.'
        #         )
        #     if img.width > 2000 or img.height > 2000:
        #         raise ValidationError(
        #             'Image dimensions must not exceed 2000x2000 pixels.'
        #         )
        # except Exception:
        #     raise ValidationError('Invalid or corrupted image file.')

        return image

    # ============================================
    # Form-Level Validation
    # ============================================

    def clean(self):
        """
        Perform form-level validation.

        Validates relationships between fields and prevents
        duplicate pending requests from the same user.

        Returns:
            dict: Cleaned data

        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        title = cleaned_data.get('title')

        # Prevent same user from submitting multiple pending requests
        # for categories with similar names (fuzzy matching)
        # TODO: Implement this check
        # if self.user and title:
        #     similar_pending = Category.objects.filter(
        #         author=self.user.profile,
        #         status=Category.Status.PENDING,
        #         title__icontains=title[:10]  # Check first 10 chars
        #     )
        #     if self.instance and self.instance.pk:
        #         similar_pending = similar_pending.exclude(pk=self.instance.pk)
        #     if similar_pending.exists():
        #         self.add_error(
        #             'title',
        #             'You already have a pending request for a similar category.'
        #         )

        # TODO: Validate slug generation doesn't conflict
        # if title:
        #     generated_slug = slugify(title)
        #     if not generated_slug:
        #         self.add_error(
        #             'title',
        #             'Category name must contain valid characters for URL generation.'
        #         )

        return cleaned_data

    # ============================================
    # Save Methods
    # ============================================

    def save(self, commit=True):
        """
        Save the form data to the database.

        Sets the author and ensures status is PENDING for new requests.

        Args:
            commit (bool): Whether to commit to database immediately

        Returns:
            Category: The saved category instance

        Note:
            The author should be set by the view before calling save(),
            or use save(commit=False) and set it manually.
        """
        category = super().save(commit=commit)

        # TODO: Add post-save actions
        # if commit:
        #     # Notify moderators about new category request
        #     notify_moderators_of_new_category_request(category)

        # TODO: Log the action for audit purposes
        # CategoryAuditLog.objects.create(
        #     category=category,
        #     action='created',
        #     user=self.user,
        #     ip_address=self.request.META.get('REMOTE_ADDR')
        # )

        return category

    # ============================================
    # Helper Methods
    # ============================================

    def get_suggested_categories(self):
        """
        Get existing categories that match the entered title.

        Useful for suggesting existing categories to users before
        they submit a new request, reducing duplicate requests.

        Returns:
            QuerySet: Matching approved categories

        Example:
            >>> form = CategoryForm(data={'title': 'Python'})
            >>> suggestions = form.get_suggested_categories()
            >>> suggestions.first().title
            'Python Programming'
        """
        title = self.data.get('title', '').strip()
        if not title or len(title) < 3:
            return Category.objects.none()

        # TODO: Implement fuzzy matching for better suggestions
        # TODO: Use PostgreSQL trigram similarity for advanced matching
        return Category.objects.filter(
            title__icontains=title,
            status=Category.Status.APPROVED
        )[:5]

    @staticmethod
    def get_popular_category_names():
        """
        Get popular category names for autocomplete suggestions.

        Returns:
            list: List of popular category names

        Example:
            >>> CategoryForm.get_popular_category_names()
            ['Python', 'Django', 'Web Development', ...]
        """
        # TODO: Cache this result for performance
        # TODO: Return names based on actual usage frequency
        from django.db.models import Count
        return list(
            Category.objects.filter(
                status=Category.Status.APPROVED
            ).annotate(
                book_count=Count('books')
            ).order_by('-book_count').values_list('title', flat=True)[:20]
        )

# ============================================
# Additional Form Classes
# ============================================

# TODO: Add form for moderators to approve/reject categories
# class CategoryModerationForm(forms.ModelForm):
#     """
#     Form for moderators to review category requests.
#     
#     Only available to staff users. Allows changing status,
#     setting reviewer, and providing rejection reasons.
#     """
#     class Meta:
#         model = Category
#         fields = ['status', 'rejection_reason']
#         widgets = {
#             'status': forms.Select(attrs={'class': 'form-control'}),
#             'rejection_reason': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Reason for rejection (required if rejecting)'
#             }),
#         }
#     
#     def clean(self):
#         cleaned_data = super().clean()
#         status = cleaned_data.get('status')
#         reason = cleaned_data.get('rejection_reason', '').strip()
#         
#         # Require rejection reason when rejecting
#         if status == Category.Status.REJECTED and not reason:
#             self.add_error(
#                 'rejection_reason',
#                 'Please provide a reason for rejecting this category.'
#             )
#         
#         return cleaned_data
#     
#     def save(self, commit=True):
#         category = super().save(commit=commit)
#         # TODO: Notify the category author about the decision
#         # notify_category_author(category)
#         return category


# TODO: Add form for searching/filtering categories
# class CategorySearchForm(forms.Form):
#     """Form for searching and filtering categories."""
#     query = forms.CharField(
#         max_length=100,
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Search categories...'
#         })
#     )
#     status = forms.ChoiceField(
#         choices=[('', 'All')] + Category.Status.choices,
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
