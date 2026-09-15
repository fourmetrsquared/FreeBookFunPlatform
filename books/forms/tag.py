"""
Tag form for the MD Books Library.

This module defines the ModelForm for creating and editing tags.
Tags are simple keyword labels used to classify books and provide
flexible, user-generated categorization.

Key Features:
    - Bootstrap-styled form controls
    - Auto-exclusion of slug field (auto-generated)
    - Case-insensitive duplicate name prevention
    - Tag name normalization (strip, title case)
    - Special character validation
    - Minimum/maximum length enforcement
    - Support for bulk tag creation

Classes:
    TagForm - ModelForm for Tag model
"""

import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from books.models import Tag


# TODO: Import gettext_lazy for proper internationalization (i18n)
# from django.utils.translation import gettext_lazy as _


class TagForm(forms.ModelForm):
    """
    ModelForm for creating and editing tags.

    This form handles the user-facing interface for tag creation and editing.
    It automatically excludes the slug field (auto-generated from name)
    and provides Bootstrap-styled widgets with comprehensive validation.

    Excluded Fields:
        - slug: Auto-generated from name in the model's save() method

    Customizations:
        - Bootstrap form-control class on the name widget
        - Placeholder text for better UX
        - Autocomplete suggestions for existing tags

    Validation:
        - Name uniqueness (case-insensitive)
        - Name length (2-50 characters)
        - No special characters (only letters, numbers, spaces, hyphens)
        - No reserved/prohibited words
        - Name normalization (strip whitespace, title case)

    Example:
        >>> form = TagForm(data={'name': 'machine learning'})
        >>> if form.is_valid():
        ...     tag = form.save()
        ...     tag.name
        'Machine Learning'
        ...     tag.slug
        'machine-learning'
    """

    class Meta:
        """Meta configuration for the TagForm."""
        model = Tag

        # Only exclude slug - it's auto-generated from name
        exclude = ['slug']

        # TODO: Consider using explicit 'fields' list instead of 'exclude'
        # fields = ['name']

        # Widget customizations for Bootstrap styling
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tag name (e.g., Python, Web Development)',
                'maxlength': '50',
                'autofocus': True,
                'autocomplete': 'off',
                # TODO: Add AJAX autocomplete for existing tag suggestions
                # 'data-autocomplete-url': '/api/tags/search/',
                # 'data-autocomplete-min-chars': '2',
                # TODO: Add real-time duplicate checking
                # 'data-check-url': '/api/tags/check-name/',
                # TODO: Add data attributes for JavaScript validation
                # 'data-validate': 'required,minlength:2,maxlength:50,pattern:alphanumeric',
            }),
        }

        # TODO: Add help texts for better user guidance
        # help_texts = {
        #     'name': 'Enter a short, descriptive keyword. '
        #             'Use letters, numbers, spaces, or hyphens only. '
        #             'Examples: "Python", "Web Development", "Sci-Fi".',
        # }

        # TODO: Add custom labels if needed
        # labels = {
        #     'name': 'Tag Name',
        # }

        # TODO: Add custom error messages
        # error_messages = {
        #     'name': {
        #         'required': 'Please enter a tag name.',
        #         'max_length': 'Tag name is too long. Maximum 50 characters.',
        #         'unique': 'This tag already exists.',
        #     },
        # }

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing additional context like the current user
        for permission-based validation.

        Custom kwargs:
            user (User): The currently authenticated user
        """
        # Extract custom kwargs before calling super()
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # TODO: Add AJAX endpoint URL for real-time name checking
        # self.fields['name'].widget.attrs['data-check-url'] = (
        #     reverse('books:api_tag_check_name')
        # )

        # TODO: Add autocomplete endpoint for tag suggestions
        # self.fields['name'].widget.attrs['data-autocomplete-url'] = (
        #     reverse('books:api_tag_search')
        # )

        # TODO: If editing, show current slug as read-only info
        # if self.instance and self.instance.pk:
        #     self.fields['name'].help_text = (
        #         f'Current URL: /tag/{self.instance.slug}/'
        #     )

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_name(self):
        """
        Validate and normalize the tag name.

        Ensures:
            - Name is not empty or whitespace-only
            - Name is at least 2 characters long
            - Name is at most 50 characters long
            - Name contains only allowed characters (letters, numbers, spaces, hyphens)
            - Name is unique (case-insensitive)
            - Name is not a reserved/prohibited word
            - Name generates a valid slug

        Normalization:
            - Strips leading/trailing whitespace
            - Converts to title case for consistency

        Returns:
            str: Cleaned and normalized tag name

        Raises:
            ValidationError: If validation fails

        Example:
            >>> form.clean_name()  # with name='  python  '
            'Python'
            >>> form.clean_name()  # with duplicate name
            ValidationError: 'A tag with this name already exists.'
        """
        name = self.cleaned_data.get('name', '').strip()

        # Check for empty name
        if not name:
            raise ValidationError('Tag name is required.')

        # Check minimum length
        if len(name) < 2:
            raise ValidationError(
                'Tag name must be at least 2 characters long.'
            )

        # Check maximum length
        if len(name) > 50:
            raise ValidationError(
                'Tag name must be at most 50 characters long.'
            )

        # Check for allowed characters only
        # Allow: letters (any language), numbers, spaces, hyphens
        # TODO: Adjust regex based on supported languages
        if not re.match(r'^[\w\s\-]+$', name, re.UNICODE):
            raise ValidationError(
                'Tag name can only contain letters, numbers, spaces, and hyphens.'
            )

        # Check for multiple consecutive spaces or hyphens
        if re.search(r'[\s\-]{2,}', name):
            raise ValidationError(
                'Tag name cannot contain consecutive spaces or hyphens.'
            )

        # Check for leading/trailing hyphens
        if name.startswith('-') or name.endswith('-'):
            raise ValidationError(
                'Tag name cannot start or end with a hyphen.'
            )

        # Check for reserved/prohibited words
        # TODO: Make this list configurable in settings
        reserved_words = [
            'create', 'edit', 'delete', 'update', 'new', 'add',
            'list', 'detail', 'search', 'admin', 'api', 'tag',
            'tags', 'book', 'books', 'category', 'categories',
            'chapter', 'chapters', 'review', 'reviews', 'author',
            'authors', 'user', 'users', 'login', 'logout',
            'register', 'signup', 'signin', 'password', 'reset',
            'none', 'null', 'undefined', 'all', 'other', 'misc',
        ]

        if name.lower() in reserved_words:
            raise ValidationError(
                f'"{name}" is a reserved word and cannot be used as a tag name. '
                'Please choose a different name.'
            )

        # Check case-insensitive uniqueness
        queryset = Tag.objects.filter(name__iexact=name)

        # Exclude current instance if editing
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            existing_tag = queryset.first()
            raise ValidationError(
                f'A tag named "{existing_tag.name}" already exists. '
                'Please use the existing tag or choose a different name.'
            )

        # Check that the name generates a valid slug
        generated_slug = slugify(name)
        if not generated_slug:
            raise ValidationError(
                'Tag name must contain at least one character that can be '
                'used in a URL. Please include letters or numbers.'
            )

        # TODO: Check slug uniqueness as well (edge case where different
        # names generate the same slug, e.g., "C++" and "C Plus Plus")
        # slug_queryset = Tag.objects.filter(slug=generated_slug)
        # if self.instance and self.instance.pk:
        #     slug_queryset = slug_queryset.exclude(pk=self.instance.pk)
        # if slug_queryset.exists():
        #     raise ValidationError(
        #         'This tag name generates a URL that conflicts with an existing tag.'
        #     )

        # Normalize to title case for consistency
        # "python" -> "Python", "web development" -> "Web Development"
        # TODO: Make normalization strategy configurable (title, lower, or none)
        name = name.title()

        # TODO: Add profanity/inappropriate content filter
        # if contains_inappropriate_words(name):
        #     raise ValidationError('Tag name contains inappropriate language.')

        return name

    # ============================================
    # Form-Level Validation
    # ============================================

    def clean(self):
        """
        Perform form-level validation.

        Currently minimal since TagForm has only one user-editable field,
        but provides a hook for future cross-field validation.

        Returns:
            dict: Cleaned data

        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()

        # TODO: Add cross-field validation if more fields are added
        # Example: Validate name against description consistency

        # TODO: Check for similar existing tags (fuzzy matching)
        # to suggest merging instead of creating duplicates
        # name = cleaned_data.get('name', '')
        # if name:
        #     similar_tags = Tag.objects.filter(name__icontains=name[:5])
        #     if similar_tags.exists():
        #         # Add a warning (not an error) about similar tags
        #         self.add_error(
        #             None,  # Non-field error
        #             f'Similar tags exist: {", ".join(t.name for t in similar_tags[:3])}. '
        #             'Consider using an existing tag.'
        #         )

        return cleaned_data

    # ============================================
    # Save Methods
    # ============================================

    def save(self, commit=True):
        """
        Save the form data to the database.

        The slug is auto-generated by the model's save() method.

        Args:
            commit (bool): Whether to commit to database immediately

        Returns:
            Tag: The saved tag instance

        Example:
            >>> tag = form.save()
            >>> tag.name
            'Machine Learning'
            >>> tag.slug
            'machine-learning'
        """
        tag = super().save(commit=commit)

        # TODO: Add post-save actions
        # if commit:
        #     # Clear cached tag data
        #     from django.core.cache import cache
        #     cache.delete('popular_tags')
        #     cache.delete('tag_cloud')

        # TODO: Log tag creation for audit purposes
        # TagAuditLog.objects.create(
        #     tag=tag,
        #     action='created' if not self.instance.pk else 'updated',
        #     user=self.user,
        # )

        # TODO: Notify moderators if user-created tags need approval
        # if self.user and not self.user.is_staff:
        #     notify_moderators_of_new_tag(tag)

        return tag

    # ============================================
    # Helper Methods
    # ============================================

    def get_similar_tags(self, limit=5):
        """
        Get existing tags similar to the entered name.

        Useful for suggesting existing tags to users before
        they create a new one, reducing tag fragmentation.

        Returns:
            QuerySet: Similar tags

        Example:
            >>> form = TagForm(data={'name': 'Python'})
            >>> similar = form.get_similar_tags()
            >>> similar.first().name
            'Python 3'
        """
        name = self.data.get('name', '').strip()
        if not name or len(name) < 2:
            return Tag.objects.none()

        # TODO: Implement fuzzy matching for better suggestions
        # TODO: Use PostgreSQL trigram similarity for advanced matching
        return Tag.objects.filter(
            name__icontains=name
        ).exclude(
            pk=self.instance.pk if self.instance else None
        )[:limit]

    @staticmethod
    def get_popular_tags(limit=20):
        """
        Get popular tags for autocomplete suggestions.

        Returns:
            list: List of popular tag names

        Example:
            >>> TagForm.get_popular_tags(5)
            ['Python', 'Django', 'JavaScript', 'Web Development', 'Data Science']
        """
        # TODO: Cache this result for performance
        from django.db.models import Count

        return list(
            Tag.objects.annotate(
                book_count=Count('books')
            ).filter(
                book_count__gt=0
            ).order_by('-book_count').values_list('name', flat=True)[:limit]
        )

    @staticmethod
    def search_tags(query, limit=10):
        """
        Search tags by name for autocomplete.

        Args:
            query (str): Search query
            limit (int): Maximum number of results

        Returns:
            QuerySet: Matching tags

        Example:
            >>> results = TagForm.search_tags('py')
            >>> results.first().name
            'Python'
        """
        if not query or len(query) < 2:
            return Tag.objects.none()

        # TODO: Add full-text search for better performance
        # TODO: Use PostgreSQL trigram similarity for fuzzy matching
        return Tag.objects.filter(
            name__icontains=query
        )[:limit]

# ============================================
# Additional Form Classes
# ============================================

# TODO: Add form for bulk tag creation
# class BulkTagForm(forms.Form):
#     """
#     Form for creating multiple tags at once.
#     
#     Accepts comma-separated tag names and creates them all.
#     Useful when setting up initial tags or importing from other systems.
#     
#     Example input: "Python, Django, Web Development, REST API"
#     """
#     tag_names = forms.CharField(
#         widget=forms.Textarea(attrs={
#             'class': 'form-control',
#             'rows': 3,
#             'placeholder': 'Enter tag names separated by commas\n'
#                           'e.g., Python, Django, Web Development',
#         }),
#         help_text='Enter multiple tag names separated by commas.'
#     )
#     
#     def clean_tag_names(self):
#         """Parse and validate comma-separated tag names."""
#         raw_input = self.cleaned_data.get('tag_names', '')
#         names = [name.strip() for name in raw_input.split(',') if name.strip()]
#         
#         if not names:
#             raise ValidationError('Please enter at least one tag name.')
#         
#         if len(names) > 20:
#             raise ValidationError('Maximum 20 tags can be created at once.')
#         
#         # Validate each name
#         validated_names = []
#         for name in names:
#             if len(name) < 2:
#                 raise ValidationError(f'Tag name "{name}" is too short (min 2 characters).')
#             if len(name) > 50:
#                 raise ValidationError(f'Tag name "{name}" is too long (max 50 characters).')
#             validated_names.append(name.title())
#         
#         # Check for duplicates within the input
#         if len(validated_names) != len(set(n.lower() for n in validated_names)):
#             raise ValidationError('Duplicate tag names found in your input.')
#         
#         return validated_names
#     
#     def save(self):
#         """Create all tags and return list of (tag, created) tuples."""
#         results = []
#         for name in self.cleaned_data['tag_names']:
#             tag, created = Tag.objects.get_or_create(
#                 name__iexact=name,
#                 defaults={'name': name}
#             )
#             results.append((tag, created))
#         return results


# TODO: Add form for tag merging
# class TagMergeForm(forms.Form):
#     """
#     Form for merging two tags into one.
#     
#     Moves all books from the source tag to the target tag,
#     then deletes the source tag. Only available to staff users.
#     """
#     source_tag = forms.ModelChoiceField(
#         queryset=Tag.objects.all(),
#         widget=forms.Select(attrs={'class': 'form-control'}),
#         help_text='The tag to merge FROM (will be deleted)'
#     )
#     target_tag = forms.ModelChoiceField(
#         queryset=Tag.objects.all(),
#         widget=forms.Select(attrs={'class': 'form-control'}),
#         help_text='The tag to merge INTO (will be kept)'
#     )
#     
#     def clean(self):
#         cleaned_data = super().clean()
#         source = cleaned_data.get('source_tag')
#         target = cleaned_data.get('target_tag')
#         
#         if source and target and source.pk == target.pk:
#             raise ValidationError('Source and target tags must be different.')
#         
#         return cleaned_data
#     
#     def save(self):
#         """Execute the tag merge."""
#         source = self.cleaned_data['source_tag']
#         target = self.cleaned_data['target_tag']
#         target.merge_with(source)
#         return target


# TODO: Add form for tag renaming
# class TagRenameForm(forms.ModelForm):
#     """
#     Form for renaming a tag.
#     
#     Updates the tag name and regenerates the slug.
#     Only available to staff users.
#     """
#     class Meta:
#         model = Tag
#         fields = ['name']
#         widgets = {
#             'name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'New tag name',
#             }),
#         }
#     
#     def save(self, commit=True):
#         tag = super().save(commit=False)
#         tag.slug = ''  # Force slug regeneration
#         if commit:
#             tag.save()
#         return tag


# TODO: Add form for searching/filtering tags
# class TagSearchForm(forms.Form):
#     """Form for searching and filtering tags."""
#     query = forms.CharField(
#         max_length=50,
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Search tags...',
#         })
#     )
#     sort_by = forms.ChoiceField(
#         choices=[
#             ('name', 'Alphabetical'),
#             ('popular', 'Most Popular'),
#             ('recent', 'Recently Created'),
#         ],
#         required=False,
#         initial='popular',
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     min_books = forms.IntegerField(
#         required=False,
#         min_value=0,
#         widget=forms.NumberInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Min books',
#         }),
#         help_text='Show only tags with at least this many books'
#     )
