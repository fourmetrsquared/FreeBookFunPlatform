"""
URL routing configuration for the accounts application.

This module defines URL patterns for user authentication, profile management,
and account-related operations.

URL Structure:
    /accounts/login/              → Login page
    /accounts/logout/             → Logout
    /accounts/signup/             → User registration
    /accounts/profile/            → View/edit own profile
    /accounts/profile/<username>/ → View other user's public profile
    /accounts/password/change/    → Change password
    /accounts/password/reset/     → Password reset request
    /accounts/settings/           → Account settings

Namespace: 'accounts'
Usage in templates: {% url 'accounts:profile' %}
Usage in views: reverse('accounts:profile')

Design Decisions:
    - Profile URLs use username instead of pk for SEO and security
    - Own profile at /profile/ (no parameter needed)
    - Public profiles at /profile/<username>/ (read-only)
    - All sensitive operations require authentication

TODO: Add the following routes in future iterations:
    - /accounts/verify-email/<token>/  → Email verification
    - /accounts/delete/                → Delete account
    - /accounts/activity/              → User activity history
    - /accounts/notifications/         → Notification settings
    - /accounts/sessions/              → Active sessions management
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

# URL namespace for this app
# Allows reversing URLs like: reverse('accounts:profile')
app_name = 'accounts'

urlpatterns = [
    # ============================================
    # 🔐 AUTHENTICATION
    # ============================================

    # Login page
    # URL: /accounts/login/
    # View: Django's built-in LoginView
    # Template: registration/login.html
    # Access: Public
    # TODO: Create custom LoginView with remember-me functionality
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            redirect_authenticated_user=True,
        ),
        name='login'
    ),

    # Logout
    # URL: /accounts/logout/
    # View: Django's built-in LogoutView
    # Access: Authenticated users
    # Note: POST-only in Django 5.0+ for security
    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='home',
        ),
        name='logout'
    ),

    # User registration
    # URL: /accounts/signup/
    # View: SignupView (custom)
    # Template: accounts/signup.html
    # Access: Public
    # TODO: Implement SignupView
    # path(
    #     'signup/',
    #     views.SignupView.as_view(),
    #     name='signup'
    # ),

    # ============================================
    # 👤 PROFILE MANAGEMENT
    # ============================================

    # View/edit own profile
    # URL: /accounts/profile/
    # View: ProfileView
    # Template: accounts/profile.html
    # Access: Authenticated users only
    # Note: No pk parameter - uses request.user
    path(
        'profile/',
        views.ProfileView.as_view(),
        name='profile'
    ),

    # View other user's public profile
    # URL: /accounts/profile/john-doe/
    # View: PublicProfileView
    # Template: accounts/public_profile.html
    # Access: Authenticated users (or public if you want)
    # Parameter: username (not pk for security)
    path(
        'profile/<str:username>/',
        views.PublicProfileView.as_view(),
        name='public_profile'
    ),

    # ============================================
    # 🔒 PASSWORD MANAGEMENT
    # ============================================

    # Change password
    # URL: /accounts/password/change/
    # View: Django's built-in PasswordChangeView
    # Template: accounts/password_change.html
    # Access: Authenticated users
    # TODO: Create custom template
    path(
        'password/change/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url='accounts:password_change_done',
        ),
        name='password_change'
    ),

    # Password change done
    # URL: /accounts/password/change/done/
    # View: Django's built-in PasswordChangeDoneView
    # Template: accounts/password_change_done.html
    # Access: Authenticated users
    path(
        'password/change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html',
        ),
        name='password_change_done'
    ),

    # Password reset request
    # URL: /accounts/password/reset/
    # View: Django's built-in PasswordResetView
    # Template: accounts/password_reset.html
    # Access: Public
    # TODO: Configure email backend and templates
    path(
        'password/reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            success_url='accounts:password_reset_done',
        ),
        name='password_reset'
    ),

    # Password reset done (email sent)
    # URL: /accounts/password/reset/done/
    # View: Django's built-in PasswordResetDoneView
    # Template: accounts/password_reset_done.html
    # Access: Public
    path(
        'password/reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done'
    ),

    # Password reset confirm (from email link)
    # URL: /accounts/password/reset/<uidb64>/<token>/
    # View: Django's built-in PasswordResetConfirmView
    # Template: accounts/password_reset_confirm.html
    # Access: Public (with valid token)
    path(
        'password/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='accounts:password_reset_complete',
        ),
        name='password_reset_confirm'
    ),

    # Password reset complete
    # URL: /accounts/password/reset/complete/
    # View: Django's built-in PasswordResetCompleteView
    # Template: accounts/password_reset_complete.html
    # Access: Public
    path(
        'password/reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),

    # ============================================
    # ⚙️ ACCOUNT SETTINGS (TODO)
    # ============================================

    # Account settings (email, notifications, privacy)
    # URL: /accounts/settings/
    # View: AccountSettingsView
    # Template: accounts/settings.html
    # Access: Authenticated users
    # TODO: Implement AccountSettingsView
    # path(
    #     'settings/',
    #     views.AccountSettingsView.as_view(),
    #     name='settings'
    # ),

    # Email verification
    # URL: /accounts/verify-email/<token>/
    # View: VerifyEmailView
    # Template: accounts/verify_email.html
    # Access: Public (with valid token)
    # TODO: Implement email verification system
    # path(
    #     'verify-email/<str:token>/',
    #     views.VerifyEmailView.as_view(),
    #     name='verify_email'
    # ),

    # Delete account
    # URL: /accounts/delete/
    # View: DeleteAccountView
    # Template: accounts/delete_account.html
    # Access: Authenticated users
    # TODO: Implement soft delete with confirmation
    # path(
    #     'delete/',
    #     views.DeleteAccountView.as_view(),
    #     name='delete_account'
    # ),

    # User activity history
    # URL: /accounts/activity/
    # View: ActivityView
    # Template: accounts/activity.html
    # Access: Authenticated users (own activity only)
    # TODO: Implement activity tracking
    # path(
    #     'activity/',
    #     views.ActivityView.as_view(),
    #     name='activity'
    # ),

    # Notification settings
    # URL: /accounts/notifications/
    # View: NotificationSettingsView
    # Template: accounts/notifications.html
    # Access: Authenticated users
    # TODO: Implement notification preferences
    # path(
    #     'notifications/',
    #     views.NotificationSettingsView.as_view(),
    #     name='notifications'
    # ),

    # Active sessions management
    # URL: /accounts/sessions/
    # View: SessionsView
    # Template: accounts/sessions.html
    # Access: Authenticated users
    # TODO: Implement session management (view/revoke sessions)
    # path(
    #     'sessions/',
    #     views.SessionsView.as_view(),
    #     name='sessions'
    # ),
]