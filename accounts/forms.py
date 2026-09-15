"""
Forms for user profile management.

This module defines ModelForms for editing User and Profile data.
These forms are used together in the ProfileView to allow users
to update their account information and profile details.

Forms:
    UserForm    - Edit User model fields (name, email)
    ProfileForm - Edit Profile model fields (bio, avatar, social links)

Key Features:
    - Bootstrap-styled form controls
    - Custom validation for email, avatar, social links
    - Security: excludes sensitive payment fields
    - Placeholder text for better UX
    - Help texts for user guidance
    - File size and format validation for avatar

Security:
    - Excludes stripe_customer_id and paypal_email (admin-only fields)
    - Excludes total_donated and is_supporter (calculated fields)
    - Validates avatar file size and format
    - Validates social link URLs

Usage:
    from .forms import UserForm, ProfileForm

    # In view
    user_form = UserForm(request.POST, instance=request.user)
    profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

    if user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()

TODO: Add the following forms in future iterations:
    - PasswordChangeForm      - Change password with validation
    - EmailChangeForm         - Change email with verification
    - DeleteAccountForm       - Delete account with confirmation
    - NotificationSettingsForm - Notification preferences
    - PrivacySettingsForm     - Privacy controls
"""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .models import Profile

# Use get_user_model() for flexibility with custom user models
User = get_user_model()


# ============================================
# User Form
# ============================================

class UserForm(forms.ModelForm):
    """
    Form for editing User model fields.

    Allows users to update their first name, last name, and email address.
    Username is excluded as it's typically immutable after registration.

    Fields:
        first_name (str): User's first name (max 150 characters)
        last_name (str): User's last name (max 150 characters)
        email (str): User's email address (must be unique)

    Validation:
        - Email uniqueness (case-insensitive)
        - Email format validation
        - Name length validation

    Security:
        - Username is excluded (cannot be changed)
        - Password is excluded (use separate password change form)
        - is_staff, is_superuser excluded (admin-only fields)

    Example:
        >>> form = UserForm(instance=user)
        >>> form.is_valid()
        True
        >>> form.save()
        <User: john_doe>
    """

    class Meta:
        """Meta configuration for the UserForm."""
        model = User

        # Explicitly list fields (safer than exclude)
        fields = [
            'first_name',
            'last_name',
            'email',
        ]

        # Widget customizations for Bootstrap styling
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name',
                'maxlength': '150',
                'autofocus': True,
                # TODO: Add autocomplete attribute
                # 'autocomplete': 'given-name',
            }),

            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name',
                'maxlength': '150',
                # TODO: Add autocomplete attribute
                # 'autocomplete': 'family-name',
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'maxlength': '254',
                # TODO: Add autocomplete attribute
                # 'autocomplete': 'email',
            }),
        }

        # Help texts for better user guidance
        help_texts = {
            'first_name': 'Your first name as it will appear on your profile.',
            'last_name': 'Your last name (optional).',
            'email': 'Your email address. Must be unique and valid.',
        }

        # Custom labels
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
        }

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing the current user for email uniqueness validation.

        Custom kwargs:
            current_user (User): The user being edited (for email validation)
        """
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # TODO: Make email required (Django's User model allows blank emails)
        # self.fields['email'].required = True

        # TODO: Add character counter for name fields
        # self.fields['first_name'].widget.attrs['data-counter'] = 'true'

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_first_name(self):
        """
        Validate the first name.

        Ensures:
            - Name is not empty or whitespace-only
            - Name contains only letters, spaces, hyphens, apostrophes
            - Name is at least 2 characters

        Returns:
            str: Cleaned first name

        Raises:
            ValidationError: If validation fails
        """
        first_name = self.cleaned_data.get('first_name', '').strip()

        if not first_name:
            raise ValidationError('First name is required.')

        if len(first_name) < 2:
            raise ValidationError('First name must be at least 2 characters.')

        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        # TODO: Support international characters (Cyrillic, Chinese, etc.)
        if not re.match(r"^[\w\s\-']+$", first_name, re.UNICODE):
            raise ValidationError(
                'First name can only contain letters, spaces, hyphens, and apostrophes.'
            )

        # TODO: Add profanity filter
        # if contains_profanity(first_name):
        #     raise ValidationError('First name contains inappropriate language.')

        return first_name

    def clean_last_name(self):
        """
        Validate the last name (optional).

        Returns:
            str: Cleaned last name or empty string
        """
        last_name = self.cleaned_data.get('last_name', '').strip()

        if last_name:
            # Same validation as first_name if provided
            if len(last_name) < 2:
                raise ValidationError('Last name must be at least 2 characters.')

            if not re.match(r"^[\w\s\-']+$", last_name, re.UNICODE):
                raise ValidationError(
                    'Last name can only contain letters, spaces, hyphens, and apostrophes.'
                )

        return last_name

    def clean_email(self):
        """
        Validate the email address.

        Ensures:
            - Email is not empty
            - Email format is valid
            - Email is unique (case-insensitive)

        Returns:
            str: Cleaned email address

        Raises:
            ValidationError: If validation fails
        """
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise ValidationError('Email address is required.')

        # Check uniqueness (case-insensitive)
        queryset = User.objects.filter(email__iexact=email)

        # Exclude current user if editing
        if self.current_user:
            queryset = queryset.exclude(pk=self.current_user.pk)
        elif self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError(
                'This email address is already in use. '
                'Please use a different email or log in with this account.'
            )

        # TODO: Add disposable email detection
        # disposable_domains = ['tempmail.com', '10minutemail.com', ...]
        # domain = email.split('@')[1]
        # if domain in disposable_domains:
        #     raise ValidationError('Disposable email addresses are not allowed.')

        # TODO: Add email domain validation
        # if not is_valid_email_domain(domain):
        #     raise ValidationError('Invalid email domain.')

        return email


# ============================================
# Profile Form
# ============================================

class ProfileForm(forms.ModelForm):
    """
    Form for editing Profile model fields.

    Allows users to update their avatar, bio, location, and social links.
    Excludes sensitive payment fields and auto-managed fields.

    Excluded Fields (Security & Auto-managed):
        - user: Set automatically from request.user
        - created_at: Auto-set on creation
        - updated_at: Auto-updated on save
        - total_donated: Calculated from donations
        - is_supporter: Calculated from donations
        - stripe_customer_id: Admin-only field (SECURITY)
        - paypal_email: Admin-only field (SECURITY)

    Fields:
        avatar (ImageField): Profile picture
        bio (str): Short biography
        location (str): User's location
        github_username (str): GitHub username
        youtube_channel_url (str): YouTube channel URL
        twitter_url (str): Twitter/X profile URL
        website_url (str): Personal website URL

    Validation:
        - Avatar file size (max 2MB)
        - Avatar format (JPG, PNG, GIF, WebP)
        - GitHub username format
        - Social link URL validation

    Example:
        >>> form = ProfileForm(instance=profile)
        >>> form.is_valid()
        True
        >>> form.save()
        <Profile: john_doe's Profile>
    """

    class Meta:
        """Meta configuration for the ProfileForm."""
        model = Profile

        # Exclude sensitive and auto-managed fields
        # IMPORTANT: Explicitly exclude payment fields for security!
        exclude = [
            'user',  # Set from request.user
            'created_at',  # Auto-set on creation
            'updated_at',  # Auto-updated on save
            'total_donated',  # Calculated from donations
            'is_supporter',  # Calculated from donations
            'stripe_customer_id',  # 🔒 SECURITY: Admin-only field
            'paypal_email',  # 🔒 SECURITY: Admin-only field
        ]

        # Widget customizations for Bootstrap styling
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif,image/webp',
                # TODO: Add image preview with JavaScript
                # 'data-preview': 'true',
                # TODO: Add drag-and-drop support
                # 'data-dropzone': 'true',
            }),

            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself... (max 500 characters)',
                'maxlength': '500',
                # TODO: Add character counter with JavaScript
                # 'data-counter': 'true',
            }),

            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., San Francisco, CA',
                'maxlength': '100',
            }),

            'github_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., AngelJumbo',
                'maxlength': '50',
                # TODO: Add GitHub username validation via AJAX
                # 'data-validate-github': 'true',
            }),

            'youtube_channel_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/@yourchannel',
                'maxlength': '255',
            }),

            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/yourusername',
                'maxlength': '255',
            }),

            'website_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com',
                'maxlength': '255',
            }),
        }

        # Help texts for better user guidance
        help_texts = {
            'avatar': 'Upload a profile picture (JPG, PNG, GIF, or WebP, max 2MB).',
            'bio': 'A short biography about yourself. Markdown is not supported.',
            'location': 'Your city, state, or country.',
            'github_username': 'Your GitHub username (without @).',
            'youtube_channel_url': 'Full URL to your YouTube channel.',
            'twitter_url': 'Full URL to your Twitter or X profile.',
            'website_url': 'Your personal website or blog URL.',
        }

        # Custom labels
        labels = {
            'avatar': 'Profile Picture',
            'bio': 'About Me',
            'location': 'Location',
            'github_username': 'GitHub',
            'youtube_channel_url': 'YouTube Channel',
            'twitter_url': 'Twitter/X',
            'website_url': 'Personal Website',
        }

    # ============================================
    # Form Initialization
    # ============================================

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom configurations.

        Allows passing the current user for validation.
        """
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # TODO: Make avatar optional (already is, but emphasize it)
        # self.fields['avatar'].required = False

        # TODO: Add autocomplete for location field
        # self.fields['location'].widget.attrs['data-autocomplete'] = 'true'

    # ============================================
    # Field-Level Validation
    # ============================================

    def clean_avatar(self):
        """
        Validate the avatar image.

        Ensures:
            - File size is within limits (max 2MB)
            - File format is allowed (JPG, PNG, GIF, WebP)
            - File is actually an image (MIME type check)

        Returns:
            ImageFieldFile: Cleaned avatar file

        Raises:
            ValidationError: If validation fails
        """
        avatar = self.cleaned_data.get('avatar')

        # Avatar is optional
        if not avatar:
            return avatar

        # Check file size (max 2MB)
        # TODO: Make max size configurable in settings
        max_size = 2 * 1024 * 1024  # 2MB

        if avatar.size > max_size:
            raise ValidationError(
                f'Avatar file size must be less than 2MB. '
                f'Your file is {avatar.size / (1024 * 1024):.2f}MB.'
            )

        # Check file extension
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        ext = avatar.name.split('.')[-1].lower()

        if ext not in allowed_extensions:
            raise ValidationError(
                f'Invalid image format. Allowed formats: {", ".join(allowed_extensions)}'
            )

        # TODO: Validate MIME type using python-magic for security
        # import magic
        # mime = magic.from_buffer(avatar.read(1024), mime=True)
        # avatar.seek(0)  # Reset file pointer
        # allowed_mimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        # if mime not in allowed_mimes:
        #     raise ValidationError('Invalid image file. Please upload a real image.')

        # TODO: Validate image dimensions using PIL
        # from PIL import Image
        # try:
        #     img = Image.open(avatar)
        #     img.verify()
        #     if img.width < 100 or img.height < 100:
        #         raise ValidationError(
        #             'Image dimensions must be at least 100x100 pixels.'
        #         )
        #     if img.width > 2000 or img.height > 2000:
        #         raise ValidationError(
        #             'Image dimensions must not exceed 2000x2000 pixels.'
        #         )
        # except Exception:
        #     raise ValidationError('Invalid or corrupted image file.')

        return avatar

    def clean_bio(self):
        """
        Validate the bio field.

        Ensures:
            - Bio is not just whitespace (if provided)
            - Bio doesn't contain excessive links (spam prevention)

        Returns:
            str: Cleaned bio
        """
        bio = self.cleaned_data.get('bio', '').strip()

        if bio:
            pass
        # TODO: Check for excessive links (spam prevention)
        # link_count = bio.count('http://') + bio.count('https://')
        # if link_count > 3:
        #     raise ValidationError(
        #         'Bio contains too many links. Please remove some.'
        #     )

        # TODO: Add profanity filter
        # if contains_profanity(bio):
        #     raise ValidationError('Bio contains inappropriate language.')

        # TODO: Strip HTML tags to prevent XSS
        # bio = strip_tags(bio)

        return bio

    def clean_github_username(self):
        """
        Validate the GitHub username.

        Ensures:
            - Username follows GitHub's format rules
            - Username doesn't contain invalid characters

        Returns:
            str: Cleaned GitHub username

        Raises:
            ValidationError: If validation fails
        """
        username = self.cleaned_data.get('github_username', '').strip()

        if username:
            # GitHub username rules:
            # - Alphanumeric or hyphens
            # - Cannot have multiple consecutive hyphens
            # - Cannot begin or end with a hyphen
            # - Maximum 39 characters
            # TODO: Update regex to match GitHub's actual rules
            if not re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$', username):
                raise ValidationError(
                    'Invalid GitHub username. '
                    'Username can only contain alphanumeric characters and hyphens, '
                    'cannot have multiple consecutive hyphens, '
                    'and cannot begin or end with a hyphen.'
                )

            # TODO: Verify username actually exists on GitHub via API
            # import requests
            # response = requests.get(f'https://api.github.com/users/{username}')
            # if response.status_code == 404:
            #     raise ValidationError('This GitHub username does not exist.')

        return username

    def clean_youtube_channel_url(self):
        """
        Validate the YouTube channel URL.

        Ensures:
            - URL is valid
            - URL is actually a YouTube URL

        Returns:
            str: Cleaned YouTube URL

        Raises:
            ValidationError: If validation fails
        """
        url = self.cleaned_data.get('youtube_channel_url', '').strip()

        if url:
            # Check if URL is a YouTube URL
            youtube_patterns = [
                r'^https?://(www\.)?youtube\.com/',
                r'^https?://(www\.)?youtu\.be/',
            ]

            is_youtube = any(re.match(pattern, url) for pattern in youtube_patterns)

            if not is_youtube:
                raise ValidationError(
                    'Please enter a valid YouTube channel URL. '
                    'Example: https://youtube.com/@yourchannel'
                )

        return url

    def clean_twitter_url(self):
        """
        Validate the Twitter/X URL.

        Ensures:
            - URL is valid
            - URL is actually a Twitter/X URL

        Returns:
            str: Cleaned Twitter URL

        Raises:
            ValidationError: If validation fails
        """
        url = self.cleaned_data.get('twitter_url', '').strip()

        if url:
            # Check if URL is a Twitter/X URL
            twitter_patterns = [
                r'^https?://(www\.)?twitter\.com/',
                r'^https?://(www\.)?x\.com/',
            ]

            is_twitter = any(re.match(pattern, url) for pattern in twitter_patterns)

            if not is_twitter:
                raise ValidationError(
                    'Please enter a valid Twitter or X profile URL. '
                    'Example: https://twitter.com/yourusername'
                )

        return url

    def clean_website_url(self):
        """
        Validate the personal website URL.

        Ensures:
            - URL is valid format
            - URL uses http or https protocol

        Returns:
            str: Cleaned website URL

        Raises:
            ValidationError: If validation fails
        """
        url = self.cleaned_data.get('website_url', '').strip()

        if url:
            # Use Django's URLValidator
            validator = URLValidator()
            try:
                validator(url)
            except ValidationError:
                raise ValidationError('Please enter a valid URL.')

            # Ensure URL uses http or https
            if not url.startswith(('http://', 'https://')):
                raise ValidationError('URL must start with http:// or https://')

        return url

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
        """
        cleaned_data = super().clean()

        # TODO: Add cross-field validation
        # Example: If location is provided, validate it's a real place
        # location = cleaned_data.get('location')
        # if location and not is_valid_location(location):
        #     self.add_error('location', 'Please enter a valid location.')

        # TODO: Check for excessive social links (spam prevention)
        # social_count = sum(1 for field in [
        #     cleaned_data.get('github_username'),
        #     cleaned_data.get('youtube_channel_url'),
        #     cleaned_data.get('twitter_url'),
        #     cleaned_data.get('website_url'),
        # ] if field)
        # if social_count > 5:
        #     self.add_error(None, 'Too many social links. Please remove some.')

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
            Profile: The saved profile instance
        """
        profile = super().save(commit=commit)

        # TODO: Add post-save actions
        # if commit:
        #     # Resize avatar if needed
        #     if self.cleaned_data.get('avatar'):
        #         resize_avatar(profile.avatar)

        # TODO: Clear cached profile data
        # from django.core.cache import cache
        # cache.delete(f'profile_{profile.id}')

        # TODO: Log the profile update
        # ProfileAuditLog.objects.create(
        #     profile=profile,
        #     action='updated',
        #     user=self.current_user,
        # )

        return profile

# ============================================
# Additional Form Classes (TODO)
# ============================================

# TODO: Add password change form
# class PasswordChangeForm(forms.Form):
#     """Form for changing user password."""
#     current_password = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Current password',
#         })
#     )
#     new_password = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'New password',
#         }),
#         help_text='Password must be at least 8 characters long.'
#     )
#     confirm_password = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Confirm new password',
#         })
#     )
#     
#     def clean(self):
#         cleaned_data = super().clean()
#         new_password = cleaned_data.get('new_password')
#         confirm_password = cleaned_data.get('confirm_password')
#         
#         if new_password and confirm_password:
#             if new_password != confirm_password:
#                 raise ValidationError('Passwords do not match.')
#         
#         return cleaned_data


# TODO: Add email change form with verification
# class EmailChangeForm(forms.Form):
#     """Form for changing email with verification."""
#     new_email = forms.EmailField(
#         widget=forms.EmailInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'New email address',
#         })
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Confirm your password',
#         }),
#         help_text='Required for security.'
#     )


# TODO: Add account deletion form
# class DeleteAccountForm(forms.Form):
#     """Form for deleting user account."""
#     confirmation = forms.CharField(
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Type "DELETE" to confirm',
#         }),
#         help_text='Type "DELETE" to confirm account deletion.'
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Confirm your password',
#         })
#     )
#     
#     def clean_confirmation(self):
#         confirmation = self.cleaned_data.get('confirmation', '')
#         if confirmation != 'DELETE':
#             raise ValidationError('Please type "DELETE" to confirm.')
#         return confirmation
