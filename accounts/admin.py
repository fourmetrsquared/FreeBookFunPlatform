"""
Django Admin configuration for the accounts application.

This module registers the Profile model with the Django admin interface
and customizes its display, filtering, search, and editing capabilities.

Registered Models:
    - ProfileAdmin - User profile management with donation tracking

Admin Features:
    - Avatar thumbnail display
    - Social links as clickable icons
    - Supporter badges for donors
    - Related content counts (books, reviews)
    - Custom actions for supporter management
    - Advanced search and filtering
    - Read-only statistics display

Usage:
    Access the admin at: /admin/
    Login with superuser credentials to manage profiles.

TODO: Add the following features in future iterations:
    - Custom admin dashboard with user statistics
    - Bulk email sending to users
    - User activity timeline in admin
    - Donation history view
    - Session management interface
"""

from django.contrib import admin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html

from .models import Profile


# ============================================
# Profile Admin
# ============================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for Profile model.

    Features:
        - Comprehensive list display with avatar, user info, and stats
        - Advanced filtering (supporter status, location, creation date)
        - Full-text search (user, bio, social links)
        - Custom actions (make/remove supporter)
        - Read-only statistics (books, reviews, donations)
        - Visual badges for supporters
        - Clickable social links
        - Avatar thumbnails

    List Display:
        - Avatar thumbnail
        - User (linked to User admin)
        - Supporter badge (if applicable)
        - Books count
        - Reviews count
        - Total donated
        - Location
        - Social links icons
        - Member since date

    Filters:
        - is_supporter (supporters only)
        - location
        - created_at (date hierarchy)

    Search:
        - user__username
        - user__email
        - user__first_name
        - user__last_name
        - bio
        - location
        - github_username

    Actions:
        - make_supporters: Mark selected profiles as supporters
        - remove_supporters: Remove supporter status
        - reset_donations: Reset donation totals to 0

    TODO: Add email notification on supporter status change
    TODO: Add donation history inline
    TODO: Add user activity timeline
    """

    # List display configuration
    list_display = (
        'avatar_thumbnail',
        'user_link',
        'supporter_badge',
        'books_count_display',
        'reviews_count_display',
        'total_donated_display',
        'location_display',
        'social_links_display',
        'member_since',
    )

    # List filters (right sidebar)
    list_filter = (
        'is_supporter',
        'location',
        'created_at',
    )

    # Search fields
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'bio',
        'location',
        'github_username',
    )

    # Raw ID fields for OneToOne relationship (shows ID input instead of dropdown)
    raw_id_fields = ('user',)

    # Read-only fields (auto-managed or calculated)
    readonly_fields = (
        'user_link',
        'created_at',
        'updated_at',
        'total_donated',
        'is_supporter',
        'books_count_display',
        'reviews_count_display',
        'categories_count_display',
        'member_since_display',
        'avatar_preview',
        'social_links_preview',
    )

    # Date hierarchy navigation
    date_hierarchy = 'created_at'

    # Ordering
    ordering = ('-created_at',)

    # List per page
    list_per_page = 25

    # Fieldsets for organized editing
    fieldsets = (
        ('User Information', {
            'fields': ('user_link', 'avatar', 'avatar_preview'),
            'description': 'Core user information and profile picture.',
        }),
        ('Profile Details', {
            'fields': ('bio', 'location'),
            'description': 'Personal information visible on the profile.',
        }),
        ('Social Links', {
            'fields': (
                'github_username',
                'youtube_channel_url',
                'twitter_url',
                'website_url',
            ),
            'description': 'Social media and website links.',
        }),
        ('Donation & Payment (Admin Only)', {
            'fields': (
                'stripe_customer_id',
                'paypal_email',
                'total_donated',
                'is_supporter',
            ),
            'classes': ('collapse',),
            'description': 'Payment and donation tracking. Only visible to admins.',
        }),
        ('Statistics (Read-only)', {
            'fields': (
                'books_count_display',
                'reviews_count_display',
                'categories_count_display',
                'member_since_display',
            ),
            'classes': ('collapse',),
            'description': 'Auto-calculated statistics.',
        }),
        ('Timestamps (Read-only)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # Custom actions
    actions = [
        'make_supporters',
        'remove_supporters',
        'reset_donations',
        'export_profiles_csv',
    ]

    # ============================================
    # Custom List Display Methods
    # ============================================

    def avatar_thumbnail(self, obj):
        """
        Display profile avatar as small thumbnail.

        Shows the user's avatar image or a default placeholder.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML img tag or placeholder div
        """
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; '
                'object-fit: cover; border-radius: 50%;" />',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; background: #ddd; '
            'border-radius: 50%; display: flex; align-items: center; '
            'justify-content: center; font-size: 18px;">{}</div>',
            obj.user.username[0].upper()
        )

    avatar_thumbnail.short_description = 'Avatar'

    def user_link(self, obj):
        """
        Display user as link to User admin page.

        Shows username with email on hover.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML link to User admin
        """
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html(
                '<a href="{}" title="{}"><strong>{}</strong></a>',
                url,
                obj.user.email,
                obj.user.username
            )
        return '—'

    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'

    def supporter_badge(self, obj):
        """
        Display supporter badge if user is a donor.

        Shows a gold star badge for supporters.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML badge or empty string
        """
        if obj.is_supporter:
            return format_html(
                '<span style="background: #ffc107; color: black; '
                'padding: 3px 8px; border-radius: 3px; font-size: 11px;">'
                '⭐ Supporter</span>'
            )
        return ''

    supporter_badge.short_description = 'Status'
    supporter_badge.admin_order_field = 'is_supporter'

    def books_count_display(self, obj):
        """
        Display count of books authored by this user.

        Shows link to filtered book list in admin.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML link with book count
        """
        count = getattr(obj, 'books_count', obj.books.count())
        if count > 0:
            url = reverse('admin:books_book_changelist') + f'?author__id__exact={obj.pk}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'

    books_count_display.short_description = 'Books'
    books_count_display.admin_order_field = 'books_count'

    def reviews_count_display(self, obj):
        """
        Display count of reviews written by this user.

        Shows link to filtered review list in admin.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML link with review count
        """
        count = getattr(obj, 'reviews_count', obj.reviews.count())
        if count > 0:
            url = reverse('admin:books_review_changelist') + f'?author__id__exact={obj.pk}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'

    reviews_count_display.short_description = 'Reviews'
    reviews_count_display.admin_order_field = 'reviews_count'

    def total_donated_display(self, obj):
        """
        Display total donated amount with currency formatting.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: Formatted currency amount
        """
        if obj.total_donated > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">${}</span>',
                f'{obj.total_donated:.2f}'
            )
        return '$0.00'

    total_donated_display.short_description = 'Donated'
    total_donated_display.admin_order_field = 'total_donated'

    def location_display(self, obj):
        """
        Display location with icon.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML with location icon and text
        """
        if obj.location:
            return format_html('📍 {}', obj.location)
        return format_html('<span style="color: #999;">—</span>')

    location_display.short_description = 'Location'
    location_display.admin_order_field = 'location'

    def social_links_display(self, obj):
        """
        Display social links as clickable icons.

        Shows icons for GitHub, YouTube, Twitter, and website.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML with social link icons
        """
        icons = []

        if obj.github_username:
            icons.append(format_html(
                '<a href="https://github.com/{}" target="_blank" '
                'title="GitHub: {}" style="margin-right: 5px;">🐙</a>',
                obj.github_username,
                obj.github_username
            ))

        if obj.youtube_channel_url:
            icons.append(format_html(
                '<a href="{}" target="_blank" title="YouTube" '
                'style="margin-right: 5px;">📺</a>',
                obj.youtube_channel_url
            ))

        if obj.twitter_url:
            icons.append(format_html(
                '<a href="{}" target="_blank" title="Twitter/X" '
                'style="margin-right: 5px;">🐦</a>',
                obj.twitter_url
            ))

        if obj.website_url:
            icons.append(format_html(
                '<a href="{}" target="_blank" title="Website" '
                'style="margin-right: 5px;">🌐</a>',
                obj.website_url
            ))

        if icons:
            return format_html(' '.join(icons))
        return format_html('<span style="color: #999;">No links</span>')

    social_links_display.short_description = 'Social'

    def member_since(self, obj):
        """
        Display member since date in short format.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: Formatted date
        """
        return obj.created_at.strftime('%Y-%m-%d')

    member_since.short_description = 'Member Since'
    member_since.admin_order_field = 'created_at'

    # ============================================
    # Read-only Field Display Methods
    # ============================================

    def avatar_preview(self, obj):
        """
        Display large avatar preview in edit form.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML img tag or placeholder
        """
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return format_html(
                '<img src="{}" style="width: 150px; height: 150px; '
                'object-fit: cover; border-radius: 50%;" />',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 150px; height: 150px; background: #ddd; '
            'border-radius: 50%; display: flex; align-items: center; '
            'justify-content: center; font-size: 48px;">{}</div>',
            obj.user.username[0].upper()
        )

    avatar_preview.short_description = 'Avatar Preview'

    def social_links_preview(self, obj):
        """
        Display all social links in edit form.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: HTML with all social links
        """
        links = []

        if obj.github_username:
            links.append(format_html(
                '<p><strong>GitHub:</strong> '
                '<a href="https://github.com/{}" target="_blank">{}</a></p>',
                obj.github_username,
                obj.github_username
            ))

        if obj.youtube_channel_url:
            links.append(format_html(
                '<p><strong>YouTube:</strong> '
                '<a href="{}" target="_blank">{}</a></p>',
                obj.youtube_channel_url,
                obj.youtube_channel_url
            ))

        if obj.twitter_url:
            links.append(format_html(
                '<p><strong>Twitter:</strong> '
                '<a href="{}" target="_blank">{}</a></p>',
                obj.twitter_url,
                obj.twitter_url
            ))

        if obj.website_url:
            links.append(format_html(
                '<p><strong>Website:</strong> '
                '<a href="{}" target="_blank">{}</a></p>',
                obj.website_url,
                obj.website_url
            ))

        if links:
            return format_html(''.join(links))
        return 'No social links provided.'

    social_links_preview.short_description = 'Social Links'

    def categories_count_display(self, obj):
        """
        Display count of category requests made by this user.

        Args:
            obj (Profile): The profile instance

        Returns:
            int: Number of category requests
        """
        return obj.category_requests.count()

    categories_count_display.short_description = 'Category Requests'

    def member_since_display(self, obj):
        """
        Display full member since date and time.

        Args:
            obj (Profile): The profile instance

        Returns:
            str: Formatted datetime
        """
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')

    member_since_display.short_description = 'Member Since'

    # ============================================
    # Query Optimization
    # ============================================

    def get_queryset(self, request):
        """
        Optimize queryset with annotations and select_related.

        Prevents N+1 queries for user, books, and reviews.

        Args:
            request: The HTTP request

        Returns:
            QuerySet: Optimized queryset
        """
        return super().get_queryset(request).select_related(
            'user'
        ).annotate(
            books_count=Count('books', filter=Q(books__is_published=True)),
            reviews_count=Count('reviews'),
        )

    # ============================================
    # Custom Admin Actions
    # ============================================

    @admin.action(description='Mark selected profiles as supporters')
    def make_supporters(self, request, queryset):
        """
        Mark selected profiles as supporters.

        Sets is_supporter=True for selected profiles.

        Args:
            request: The HTTP request
            queryset: Selected profiles
        """
        updated = queryset.update(is_supporter=True)
        self.message_user(
            request,
            f'{updated} profile(s) marked as supporters.',
            level='success'
        )

        # TODO: Send email notification to users
        # for profile in queryset:
        #     send_supporter_notification(profile.user.email)

    @admin.action(description='Remove supporter status from selected profiles')
    def remove_supporters(self, request, queryset):
        """
        Remove supporter status from selected profiles.

        Sets is_supporter=False for selected profiles.

        Args:
            request: The HTTP request
            queryset: Selected profiles
        """
        updated = queryset.update(is_supporter=False)
        self.message_user(
            request,
            f'{updated} profile(s) removed from supporters.',
            level='warning'
        )

    @admin.action(description='Reset donation totals to $0.00')
    def reset_donations(self, request, queryset):
        """
        Reset donation totals to zero.

        Sets total_donated=0 and is_supporter=False.
        WARNING: This action cannot be undone!

        Args:
            request: The HTTP request
            queryset: Selected profiles
        """
        updated = queryset.update(total_donated=0, is_supporter=False)
        self.message_user(
            request,
            f'Donation totals reset for {updated} profile(s).',
            level='warning'
        )

    @admin.action(description='Export selected profiles to CSV')
    def export_profiles_csv(self, request, queryset):
        """
        Export selected profiles to CSV file.

        Creates a CSV file with profile data for download.

        Args:
            request: The HTTP request
            queryset: Selected profiles

        TODO: Implement CSV export
        """
        # TODO: Implement CSV export
        # import csv
        # from django.http import HttpResponse
        # 
        # response = HttpResponse(content_type='text/csv')
        # response['Content-Disposition'] = 'attachment; filename="profiles.csv"'
        # 
        # writer = csv.writer(response)
        # writer.writerow(['Username', 'Email', 'Location', 'Total Donated', 'Member Since'])
        # 
        # for profile in queryset:
        #     writer.writerow([
        #         profile.user.username,
        #         profile.user.email,
        #         profile.location,
        #         profile.total_donated,
        #         profile.created_at.strftime('%Y-%m-%d'),
        #     ])
        # 
        # return response

        self.message_user(
            request,
            'CSV export is not yet implemented.',
            level='info'
        )

# ============================================
# Admin Site Customization
# ============================================

# The admin site header is already set in books/admin.py
# No need to set it again here
