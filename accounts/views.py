"""
Views for user profile management.

Contains classes for viewing and editing user profiles.
Profiles extend the base User model with additional information
like bio, avatar, and social links.

Classes:
    ProfileView         - View and edit own profile
    PublicProfileView   - View other users' public profiles
    ProfileSettingsView - Account settings (email, password)

Key Features:
    - Authentication required for all profile operations
    - Permission checks (only owner or staff can edit)
    - Auto-creation of Profile if missing
    - PRG pattern (redirect after POST)
    - Flash messages for user feedback
    - Image upload with validation

Security:
    - LoginRequiredMixin on all views
    - Owner-only edit permissions
    - Input validation on forms
    - CSRF protection (automatic with forms)

TODO: Add the following views in future iterations:
    - AvatarCropView        - Crop uploaded avatar images
    - ProfilePasswordView   - Change password
    - ProfileEmailView      - Change email with verification
    - ProfileDeleteView     - Delete account (soft delete)
    - ProfileActivityView   - User's activity history
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import DetailView

from .forms import UserForm, ProfileForm
from .models import Profile

User = get_user_model()


# ============================================
# Profile View (Edit Own Profile)
# ============================================

class ProfileView(LoginRequiredMixin, View):
    """
    View and edit the current user's profile.

    GET /profile/        → Show profile with edit forms
    POST /profile/       → Update profile and redirect

    Context:
        user_form: UserForm - form for User model fields
        profile_form: ProfileForm - form for Profile model fields
        profile: Profile - the profile object

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Auto-creates Profile if missing
        - Validates both forms before saving
        - Redirects after successful save (PRG pattern)
        - Shows success/error messages

    Security:
        - Only the profile owner can edit
        - URL uses current user (no pk parameter needed)
        - CSRF protection via Django forms

    Permissions:
        - Owner: full edit access
        - Other users: redirected to own profile
        - Anonymous: redirected to login

    Example:
        GET /profile/
        → Shows forms pre-filled with current user's data

        POST /profile/
        → Validates and saves, redirects to /profile/
    """
    template_name = 'accounts/profile.html'

    def get_profile(self, user):
        """
        Get or create the user's profile.

        Args:
            user (User): The user to get profile for

        Returns:
            Profile: The user's profile (created if missing)
        """
        profile, created = Profile.objects.get_or_create(user=user)

        if created:
            messages.info(
                self.request if hasattr(self, 'request') else None,
                'Welcome! Please complete your profile.'
            )

        return profile

    def get(self, request):
        """
        Handle GET request - show profile forms.

        Args:
            request (HttpRequest): The HTTP request object

        Returns:
            HttpResponse: Rendered profile page with forms
        """
        profile = self.get_profile(request.user)

        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'is_own_profile': True,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        """
        Handle POST request - update profile.

        Validates both forms and saves if valid.
        Redirects to profile page after save (PRG pattern).

        Args:
            request (HttpRequest): The HTTP request object

        Returns:
            HttpResponse: Redirect to profile page
        """
        profile = self.get_profile(request.user)

        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        # Validate both forms
        if user_form.is_valid() and profile_form.is_valid():
            # Save both forms
            user_form.save()
            profile_form.save()

            messages.success(
                request,
                'Your profile has been updated successfully!'
            )

            # Redirect to prevent duplicate submissions (PRG pattern)
            return redirect('accounts:profile')

        # Forms invalid - show errors
        messages.error(
            request,
            'Please correct the errors below.'
        )

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'is_own_profile': True,
        }

        return render(request, self.template_name, context)


# ============================================
# Public Profile View (View Other Users)
# ============================================

class PublicProfileView(LoginRequiredMixin, DetailView):
    """
    View another user's public profile (read-only).

    GET /profile/<username>/

    Context:
        profile: Profile - the user's profile
        profile_user: User - the user object
        user_books: QuerySet - books by this user
        user_reviews: QuerySet - reviews by this user
        can_edit: bool - whether current user can edit this profile

    Features:
        - Shows public information only
        - Displays user's books and reviews
        - Edit button if viewing own profile
        - Follow button (TODO)

    Security:
        - Returns 404 for non-existent users
        - No edit capability for other users

    TODO: Add follow/unfollow functionality
    TODO: Add user activity timeline
    """
    model = Profile
    template_name = 'accounts/public_profile.html'
    context_object_name = 'profile'
    slug_field = 'user__username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        """Optimize queries for related data."""
        return Profile.objects.select_related('user')

    def get_object(self, queryset=None):
        """Get the profile by username."""
        if queryset is None:
            queryset = self.get_queryset()

        username = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(queryset, user__username=username)

    def get_context_data(self, **kwargs):
        """Add user's content and permissions to context."""
        context = super().get_context_data(**kwargs)
        profile = self.object

        # User's published books
        from books.models import Book
        context['user_books'] = Book.objects.filter(
            author=profile,
            is_published=True
        ).order_by('-created_at')[:10]

        # User's recent reviews
        from books.models import Review
        context['user_reviews'] = Review.objects.filter(
            author=profile
        ).select_related('book').order_by('-created_at')[:5]

        # Statistics
        context['book_count'] = Book.objects.filter(
            author=profile,
            is_published=True
        ).count()
        context['review_count'] = Review.objects.filter(author=profile).count()

        # Permission check
        context['can_edit'] = (
                self.request.user.is_authenticated and
                (profile.user == self.request.user or self.request.user.is_staff)
        )

        # Check if viewing own profile
        context['is_own_profile'] = (
                self.request.user.is_authenticated and
                profile.user == self.request.user
        )

        return context

# ============================================
# Alternative: Class-Based UpdateView Approach
# ============================================

# TODO: Consider using UpdateView for cleaner code
# class ProfileUpdateView(LoginRequiredMixin, UpdateView):
#     """
#     Alternative implementation using UpdateView.
#     
#     Pros:
#         - Less code
#         - Built-in form handling
#         - Automatic redirect after save
#     
#     Cons:
#         - Harder to handle two forms (User + Profile)
#         - Less control over validation flow
#     """
#     model = Profile
#     form_class = ProfileForm
#     template_name = 'accounts/profile.html'
#     success_url = reverse_lazy('accounts:profile')
#     
#     def get_object(self, queryset=None):
#         """Get current user's profile."""
#         profile, created = Profile.objects.get_or_create(
#             user=self.request.user
#         )
#         return profile
#     
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Add UserForm to context
#         if self.request.POST:
#             context['user_form'] = UserForm(
#                 self.request.POST,
#                 instance=self.request.user
#             )
#         else:
#             context['user_form'] = UserForm(instance=self.request.user)
#         return context
#     
#     def form_valid(self, form):
#         """Validate and save both forms."""
#         context = self.get_context_data()
#         user_form = context['user_form']
#         
#         if user_form.is_valid() and form.is_valid():
#             user_form.save()
#             form.save()
#             messages.success(self.request, 'Profile updated!')
#             return super().form_valid(form)
#         else:
#             return self.render_to_response(context)


# ============================================
# Helper Functions
# ============================================

# TODO: Add helper functions for common operations

# def get_user_profile_or_404(username):
#     """
#     Get a user's profile by username.
#     
#     Args:
#         username (str): The username to look up
#     
#     Returns:
#         Profile: The user's profile
#     
#     Raises:
#         Http404: If user or profile doesn't exist
#     """
#     user = get_object_or_404(User, username=username)
#     return get_object_or_404(Profile, user=user)


# def can_edit_profile(viewer, profile_owner):
#     """
#     Check if viewer can edit profile_owner's profile.
#     
#     Args:
#         viewer (User): The user trying to edit
#         profile_owner (User): The profile owner
#     
#     Returns:
#         bool: True if viewer can edit
#     """
#     if not viewer.is_authenticated:
#         return False
#     return viewer == profile_owner or viewer.is_staff
