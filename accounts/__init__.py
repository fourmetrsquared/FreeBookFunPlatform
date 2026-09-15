"""
Accounts package for the MD Books Library.

This package handles user authentication, registration, and profile management.
It's organized into sub-packages for better code organization as the app grows.

Sub-packages:
    models/   - Profile model and related models
    forms/    - User and Profile forms
    views/    - Profile and authentication views

Public API:
    Profile         - User profile model
    UserForm        - Form for editing User fields
    ProfileForm     - Form for editing Profile fields
    ProfileView     - View/edit own profile
    PublicProfileView - View other users' profiles

Usage:
    from accounts import Profile, UserForm, ProfileForm
    from accounts import ProfileView, PublicProfileView
"""

# Import from forms sub-package
from .forms import UserForm, ProfileForm
# Import from models sub-package
from .models import Profile
# Import from views sub-package
from .views import ProfileView, PublicProfileView

# Define public API
__all__ = [
    # Models
    'Profile',

    # Forms
    'UserForm',
    'ProfileForm',

    # Views
    'ProfileView',
    'PublicProfileView',
]

# TODO: Add additional imports as the app grows
# from .models import (
#     Profile,
#     EmailVerification,
#     Session,
# )
# from .forms import (
#     UserForm,
#     ProfileForm,
#     PasswordChangeForm,
#     EmailChangeForm,
# )
# from .views import (
#     ProfileView,
#     PublicProfileView,
#     LoginView,
#     LogoutView,
#     SignupView,
# )
