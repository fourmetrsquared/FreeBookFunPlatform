"""
Django Admin configuration for the books application.

This module registers all models with the Django admin interface and
customizes their display, filtering, search, and editing capabilities.

Registered Models:
    - BookAdmin         - Main book management with inline chapters
    - CategoryAdmin     - Category requests with approval workflow
    - ChapterAdmin      - Chapter management within books
    - ReviewAdmin       - Review moderation and viewing
    - TagAdmin          - Tag management with book counts

Admin Features:
    - Custom list displays with relevant fields
    - Advanced filtering and search capabilities
    - Inline editing for related models
    - Custom admin actions (approve, publish, etc.)
    - Prepopulated slug fields
    - Read-only auto-managed fields
    - Date-based navigation

Usage:
    Access the admin at: /admin/
    Login with superuser credentials to manage content.

TODO: Add the following features in future iterations:
    - Custom admin dashboard with statistics
    - Bulk import/export functionality
    - Advanced reporting and analytics
    - Custom admin views for moderation queue
    - Admin actions for notifications
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import Book, Category, Chapter, Review, Tag


# ============================================
# Inline Admin Classes
# ============================================

class ChapterInline(admin.TabularInline):
    """
    Inline editor for chapters within the Book admin.

    Allows adding/editing chapters directly on the book edit page
    without navigating to a separate page.

    Features:
        - Tabular display for compact view
        - Show 3 extra empty forms for quick chapter addition
        - Prepopulated slug from title
        - Ordering by chapter order

    TODO: Add word count display
    TODO: Add Markdown preview link
    """
    model = Chapter
    extra = 3
    fields = ('title', 'slug', 'order', 'is_published')
    readonly_fields = ('slug',)
    ordering = ('order',)

    # TODO: Add verbose name for better UX
    # verbose_name = 'Chapter'
    # verbose_name_plural = 'Chapters'


class ReviewInline(admin.TabularInline):
    """
    Inline viewer for reviews within the Book admin.

    Shows reviews on the book edit page for quick reference.
    Reviews are read-only here (edit in dedicated Review admin).

    Features:
        - Read-only display (reviews edited separately)
        - Shows author, rating, and comment excerpt
        - Limited to 5 most recent reviews
    """
    model = Review
    extra = 0
    fields = ('author', 'rating', 'comment_excerpt', 'created_at')
    readonly_fields = ('author', 'rating', 'comment_excerpt', 'created_at')
    ordering = ('-created_at',)
    max_num = 5
    can_delete = False

    def comment_excerpt(self, obj):
        """Show first 100 characters of comment."""
        if obj.comment:
            return obj.comment[:100] + ('...' if len(obj.comment) > 100 else '')
        return '—'

    comment_excerpt.short_description = 'Comment'


# ============================================
# Book Admin
# ============================================

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """
    Admin interface for Book model.

    Features:
        - Comprehensive list display with key metrics
        - Advanced filtering (published status, category, author, language)
        - Full-text search (title, description, tags)
        - Inline chapter management
        - Custom actions (publish, unpublish)
        - Prepopulated slug from title
        - Read-only auto-managed fields (views, likes, timestamps)
        - Annotated fields for review stats

    List Display:
        - Cover image thumbnail
        - Title (linked to edit page)
        - Author (linked to author's profile)
        - Category
        - Views count
        - Likes count
        - Average rating (stars)
        - Published status (colored badge)
        - Created date

    Filters:
        - is_published (published/draft)
        - category
        - author
        - language
        - created_at (date hierarchy)

    Search:
        - title
        - description
        - tags__name
        - author__user__username

    Actions:
        - publish_books: Publish selected drafts
        - unpublish_books: Unpublish selected books

    TODO: Add bulk image upload
    TODO: Add reading time auto-calculation
    TODO: Add featured book flag
    """

    # List display configuration
    list_display = (
        'cover_thumbnail',
        'title_link',
        'author_link',
        'category_link',
        'views_count',
        'likes_count',
        'rating_stars',
        'status_badge',
        'created_at_short',
    )

    # List filters (right sidebar)
    list_filter = (
        'is_published',
        'category',
        'author',
        'language',
        'created_at',
    )

    # Search fields
    search_fields = (
        'title',
        'description',
        'tags__name',
        'author__user__username',
    )

    # Prepopulate slug from title
    prepopulated_fields = {'slug': ('title',)}

    # Filter horizontal for tags (M2M) - shows as dual-list selector
    filter_horizontal = ('tags',)

    # Raw ID fields for large foreign keys (shows ID input instead of dropdown)
    raw_id_fields = ('author',)

    # Read-only fields (auto-managed)
    readonly_fields = (
        'views',
        'likes',
        'created_at',
        'updated_at',
        'average_rating_display',
        'review_count_display',
        'chapter_count_display',
    )

    # Date hierarchy navigation
    date_hierarchy = 'created_at'

    # Ordering
    ordering = ('-created_at',)

    # List per page
    list_per_page = 25

    # Fieldsets for organized editing
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'image'),
            'description': 'Core book information visible to readers.',
        }),
        ('Classification', {
            'fields': ('category', 'tags', 'language'),
            'description': 'Organize the book for discovery.',
        }),
        ('Author & Publishing', {
            'fields': ('author', 'is_published', 'reading_time_minutes'),
            'description': 'Author attribution and publication status.',
        }),
        ('Statistics (Read-only)', {
            'fields': (
                'views', 'likes',
                'average_rating_display',
                'review_count_display',
                'chapter_count_display',
            ),
            'classes': ('collapse',),
            'description': 'Auto-calculated statistics.',
        }),
        ('Timestamps (Read-only)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # Inline editors
    inlines = [ChapterInline, ReviewInline]

    # Custom actions
    actions = ['publish_books', 'unpublish_books', 'reset_view_count']

    # ============================================
    # Custom List Display Methods
    # ============================================

    def cover_thumbnail(self, obj):
        """Display book cover as small thumbnail."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 60px; object-fit: cover; border-radius: 3px;" />',
                obj.image.url
            )
        return format_html(
            '<div style="width: 40px; height: 60px; background: #ddd; border-radius: 3px;"></div>'
        )

    cover_thumbnail.short_description = 'Cover'

    def title_link(self, obj):
        """Display title as link to detail page."""
        url = reverse('admin:books_book_change', args=[obj.pk])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.title)

    title_link.short_description = 'Title'
    title_link.admin_order_field = 'title'

    def author_link(self, obj):
        """Display author as link to their profile."""
        if obj.author and obj.author.user:
            url = reverse('admin:accounts_profile_change', args=[obj.author.pk])
            return format_html('<a href="{}">{}</a>', url, obj.author.user.username)
        return '—'

    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__user__username'

    def category_link(self, obj):
        """Display category as link."""
        if obj.category:
            url = reverse('admin:books_category_change', args=[obj.category.pk])
            return format_html('<a href="{}">{}</a>', url, obj.category.title)
        return format_html('<span style="color: #999;">Uncategorized</span>')

    category_link.short_description = 'Category'

    def views_count(self, obj):
        """Display views with formatting."""
        return f'{obj.views:,}'

    views_count.short_description = 'Views'
    views_count.admin_order_field = 'views'

    def likes_count(self, obj):
        """Display likes with formatting."""
        return f'{obj.likes:,}'

    likes_count.short_description = 'Likes'
    likes_count.admin_order_field = 'likes'

    def rating_stars(self, obj):
        """Display average rating as stars."""
        # TODO: Use annotated field for better performance
        avg = obj.reviews.aggregate(avg=Avg('rating'))['avg']
        if avg is None:
            return format_html('<span style="color: #999;">No ratings</span>')

        stars = '★' * int(round(avg)) + '☆' * (5 - int(round(avg)))
        return format_html(
            '<span style="color: #f5a623;">{}</span> ({:.1f})',
            stars, avg
        )

    rating_stars.short_description = 'Rating'

    def status_badge(self, obj):
        """Display published status as colored badge."""
        if obj.is_published:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">Published</span>'
            )
        return format_html(
            '<span style="background: #ffc107; color: black; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">Draft</span>'
        )

    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_published'

    def created_at_short(self, obj):
        """Display created date in short format."""
        return obj.created_at.strftime('%Y-%m-%d')

    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'

    # Read-only display methods
    def average_rating_display(self, obj):
        """Display average rating in read-only field."""
        avg = obj.reviews.aggregate(avg=Avg('rating'))['avg']
        return f'{avg:.1f} / 5.0' if avg else 'No ratings yet'

    average_rating_display.short_description = 'Average Rating'

    def review_count_display(self, obj):
        """Display review count in read-only field."""
        return obj.reviews.count()

    review_count_display.short_description = 'Review Count'

    def chapter_count_display(self, obj):
        """Display chapter count in read-only field."""
        return obj.chapters.count()

    chapter_count_display.short_description = 'Chapter Count'

    # ============================================
    # Query Optimization
    # ============================================

    def get_queryset(self, request):
        """
        Optimize queryset with annotations and select_related.

        Prevents N+1 queries for author, category, and review stats.
        """
        return super().get_queryset(request).select_related(
            'author', 'author__user', 'category'
        ).prefetch_related(
            'tags'
        ).annotate(
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating'),
            chapter_count=Count('chapters'),
        )

    # ============================================
    # Custom Admin Actions
    # ============================================

    @admin.action(description='Publish selected books')
    def publish_books(self, request, queryset):
        """
        Publish selected draft books.

        Only publishes books that have at least one chapter.
        """
        # Filter out books without chapters
        books_without_chapters = queryset.filter(chapters__isnull=True)
        if books_without_chapters.exists():
            self.message_user(
                request,
                f'{books_without_chapters.count()} book(s) skipped: no chapters.',
                level='warning'
            )
            queryset = queryset.exclude(pk__in=books_without_chapters.values_list('pk', flat=True))

        updated = queryset.update(is_published=True)
        self.message_user(
            request,
            f'{updated} book(s) published successfully.',
            level='success'
        )

    @admin.action(description='Unpublish selected books')
    def unpublish_books(self, request, queryset):
        """Unpublish selected books (move to draft)."""
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f'{updated} book(s) moved to draft.',
            level='success'
        )

    @admin.action(description='Reset view count to 0')
    def reset_view_count(self, request, queryset):
        """Reset view count for selected books."""
        updated = queryset.update(views=0)
        self.message_user(
            request,
            f'View count reset for {updated} book(s).',
            level='success'
        )

    # TODO: Add more actions
    # @admin.action(description='Feature selected books')
    # def feature_books(self, request, queryset):
    #     """Mark books as featured."""
    #     pass


# ============================================
# Category Admin
# ============================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model with approval workflow.

    Features:
        - List display with status badges
        - Filter by status (pending/approved/rejected)
        - Custom actions for bulk approval/rejection
        - Prepopulated slug from title
        - Book count annotation
        - Author and reviewer tracking

    List Display:
        - Image thumbnail
        - Title (linked)
        - Status (colored badge)
        - Book count
        - Author
        - Reviewed by
        - Created date

    Filters:
        - status
        - author
        - reviewed_by
        - created_at

    Search:
        - title
        - description
        - author__user__username

    Actions:
        - approve_categories: Approve selected pending categories
        - reject_categories: Reject selected categories

    TODO: Add rejection reason dialog in action
    TODO: Add email notification on approval/rejection
    """

    list_display = (
        'image_thumbnail',
        'title_link',
        'status_badge',
        'book_count_display',
        'author_link',
        'reviewed_by_link',
        'created_at_short',
    )

    list_filter = (
        'status',
        'author',
        'reviewed_by',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'author__user__username',
    )

    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author', 'reviewed_by')

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ('Category Information', {
            'fields': ('title', 'slug', 'description', 'image'),
        }),
        ('Request Details', {
            'fields': ('author', 'status', 'reviewed_by', 'rejection_reason'),
            'description': 'Moderation workflow fields.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_categories', 'reject_categories']

    # ============================================
    # Custom List Display Methods
    # ============================================

    def image_thumbnail(self, obj):
        """Display category image as thumbnail."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 3px;" />',
                obj.image.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: #ddd; border-radius: 3px;"></div>'
        )

    image_thumbnail.short_description = 'Image'

    def title_link(self, obj):
        """Display title as link."""
        url = reverse('admin:books_category_change', args=[obj.pk])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.title)

    title_link.short_description = 'Title'
    title_link.admin_order_field = 'title'

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': ('#ffc107', 'black', 'Pending'),
            'approved': ('#28a745', 'white', 'Approved'),
            'rejected': ('#dc3545', 'white', 'Rejected'),
        }
        bg, color, label = colors.get(obj.status, ('#6c757d', 'white', obj.status))
        return format_html(
            '<span style="background: {}; color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            bg, color, label
        )

    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def book_count_display(self, obj):
        """Display book count (from annotation)."""
        return getattr(obj, 'book_count', obj.books.count())

    book_count_display.short_description = 'Books'
    book_count_display.admin_order_field = 'book_count'

    def author_link(self, obj):
        """Display author as link."""
        if obj.author and obj.author.user:
            url = reverse('admin:accounts_profile_change', args=[obj.author.pk])
            return format_html('<a href="{}">{}</a>', url, obj.author.user.username)
        return '—'

    author_link.short_description = 'Requested By'

    def reviewed_by_link(self, obj):
        """Display reviewer as link."""
        if obj.reviewed_by and obj.reviewed_by.user:
            url = reverse('admin:accounts_profile_change', args=[obj.reviewed_by.pk])
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.user.username)
        return format_html('<span style="color: #999;">Not reviewed</span>')

    reviewed_by_link.short_description = 'Reviewed By'

    def created_at_short(self, obj):
        """Display created date in short format."""
        return obj.created_at.strftime('%Y-%m-%d')

    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'

    # ============================================
    # Query Optimization
    # ============================================

    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return super().get_queryset(request).select_related(
            'author', 'author__user', 'reviewed_by', 'reviewed_by__user'
        ).annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        )

    # ============================================
    # Custom Admin Actions
    # ============================================

    @admin.action(description='Approve selected categories')
    def approve_categories(self, request, queryset):
        """Approve selected pending categories."""
        pending = queryset.filter(status=Category.Status.PENDING)
        count = 0
        for category in pending:
            category.approve(reviewer=request.user.profile)
            count += 1

        self.message_user(
            request,
            f'{count} category(ies) approved.',
            level='success'
        )

    @admin.action(description='Reject selected categories')
    def reject_categories(self, request, queryset):
        """
        Reject selected categories.

        TODO: Add dialog for rejection reason
        """
        pending = queryset.filter(status=Category.Status.PENDING)
        count = 0
        for category in pending:
            category.reject(
                reviewer=request.user.profile,
                reason='Rejected by admin.'
            )
            count += 1

        self.message_user(
            request,
            f'{count} category(ies) rejected.',
            level='warning'
        )


# ============================================
# Chapter Admin
# ============================================

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """
    Admin interface for Chapter model.

    Features:
        - List display with book, order, title
        - Filter by book and publication status
        - Search in title and content
        - Prepopulated slug from title
        - Word count display
        - Reading time estimation

    TODO: Add Markdown preview
    TODO: Add chapter reordering interface
    """

    list_display = (
        'title_link',
        'book_link',
        'order_display',
        'word_count_display',
        'reading_time_display',
        'status_badge',
        'created_at_short',
    )

    list_filter = (
        'book',
        'is_published',
        'created_at',
    )

    search_fields = (
        'title',
        'content',
        'book__title',
    )

    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('book',)

    readonly_fields = (
        'created_at',
        'updated_at',
        'word_count_display',
        'reading_time_display',
    )

    date_hierarchy = 'created_at'
    ordering = ('book', 'order')
    list_per_page = 25

    fieldsets = (
        ('Chapter Information', {
            'fields': ('book', 'title', 'slug', 'description', 'order'),
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'Write chapter content in Markdown format.',
        }),
        ('Publication', {
            'fields': ('is_published',),
        }),
        ('Statistics', {
            'fields': ('word_count_display', 'reading_time_display'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ============================================
    # Custom List Display Methods
    # ============================================

    def title_link(self, obj):
        """Display title as link."""
        url = reverse('admin:books_chapter_change', args=[obj.pk])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.title)

    title_link.short_description = 'Title'
    title_link.admin_order_field = 'title'

    def book_link(self, obj):
        """Display book as link."""
        if obj.book:
            url = reverse('admin:books_book_change', args=[obj.book.pk])
            return format_html('<a href="{}">{}</a>', url, obj.book.title)
        return '—'

    book_link.short_description = 'Book'
    book_link.admin_order_field = 'book__title'

    def order_display(self, obj):
        """Display order with formatting."""
        return f'#{obj.order}'

    order_display.short_description = 'Order'
    order_display.admin_order_field = 'order'

    def word_count_display(self, obj):
        """Display word count."""
        count = len(obj.content.split()) if obj.content else 0
        return f'{count:,} words'

    word_count_display.short_description = 'Word Count'

    def reading_time_display(self, obj):
        """Display estimated reading time."""
        count = len(obj.content.split()) if obj.content else 0
        minutes = max(1, count // 225)
        return f'{minutes} min'

    reading_time_display.short_description = 'Reading Time'

    def status_badge(self, obj):
        """Display published status."""
        if obj.is_published:
            return format_html(
                '<span style="color: #28a745;">✓ Published</span>'
            )
        return format_html(
            '<span style="color: #ffc107;">○ Draft</span>'
        )

    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_published'

    def created_at_short(self, obj):
        """Display created date."""
        return obj.created_at.strftime('%Y-%m-%d')

    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'


# ============================================
# Review Admin
# ============================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.

    Features:
        - List display with book, author, rating
        - Filter by rating and book
        - Search in book title and author
        - Star rating display
        - Comment preview

    TODO: Add moderation actions (hide, delete)
    TODO: Add review reporting interface
    """

    list_display = (
        'book_link',
        'author_link',
        'rating_stars',
        'comment_preview',
        'created_at_short',
    )

    list_filter = (
        'rating',
        'book',
        'created_at',
    )

    search_fields = (
        'book__title',
        'author__user__username',
        'comment',
    )

    raw_id_fields = ('book', 'author')

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ('Review Information', {
            'fields': ('book', 'author', 'rating', 'comment'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ============================================
    # Custom List Display Methods
    # ============================================

    def book_link(self, obj):
        """Display book as link."""
        if obj.book:
            url = reverse('admin:books_book_change', args=[obj.book.pk])
            return format_html('<a href="{}">{}</a>', url, obj.book.title)
        return '—'

    book_link.short_description = 'Book'
    book_link.admin_order_field = 'book__title'

    def author_link(self, obj):
        """Display author as link."""
        if obj.author and obj.author.user:
            url = reverse('admin:accounts_profile_change', args=[obj.author.pk])
            return format_html('<a href="{}">{}</a>', url, obj.author.user.username)
        return '—'

    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__user__username'

    def rating_stars(self, obj):
        """Display rating as stars."""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: #f5a623; font-size: 16px;">{}</span>',
            stars
        )

    rating_stars.short_description = 'Rating'
    rating_stars.admin_order_field = 'rating'

    def comment_preview(self, obj):
        """Display first 50 characters of comment."""
        if obj.comment:
            preview = obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
            return preview
        return format_html('<span style="color: #999;">No comment</span>')

    comment_preview.short_description = 'Comment'

    def created_at_short(self, obj):
        """Display created date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'


# ============================================
# Tag Admin
# ============================================

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin interface for Tag model.

    Features:
        - List display with name and book count
        - Search by name
        - Prepopulated slug from name
        - Book count annotation

    TODO: Add tag merging interface
    TODO: Add tag synonyms management
    """

    list_display = (
        'name_link',
        'book_count_display',
        'created_at_short',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'name',
    )

    prepopulated_fields = {'slug': ('name',)}

    readonly_fields = (
        'created_at',
        'updated_at',
        'book_count_display',
    )

    date_hierarchy = 'created_at'
    ordering = ('name',)
    list_per_page = 50

    fieldsets = (
        ('Tag Information', {
            'fields': ('name', 'slug'),
        }),
        ('Statistics', {
            'fields': ('book_count_display',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ============================================
    # Custom List Display Methods
    # ============================================

    def name_link(self, obj):
        """Display name as link."""
        url = reverse('admin:books_tag_change', args=[obj.pk])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.name)

    name_link.short_description = 'Name'
    name_link.admin_order_field = 'name'

    def book_count_display(self, obj):
        """Display book count (from annotation)."""
        count = getattr(obj, 'book_count', obj.books.count())
        return f'{count:,} books'

    book_count_display.short_description = 'Books'
    book_count_display.admin_order_field = 'book_count'

    def created_at_short(self, obj):
        """Display created date."""
        return obj.created_at.strftime('%Y-%m-%d')

    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'

    # ============================================
    # Query Optimization
    # ============================================

    def get_queryset(self, request):
        """Optimize queryset with book count annotation."""
        return super().get_queryset(request).annotate(
            book_count=Count('books', filter=Q(books__is_published=True))
        )


# ============================================
# Admin Site Customization
# ============================================

# Customize admin site header and title
admin.site.site_header = 'MD Books Library Administration'
admin.site.site_title = 'MD Books Admin'
admin.site.index_title = 'Dashboard'

# TODO: Add custom admin index view with statistics
# class CustomAdminSite(admin.AdminSite):
#     def index(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         # Add custom statistics
#         extra_context['total_books'] = Book.objects.filter(is_published=True).count()
#         extra_context['pending_categories'] = Category.objects.filter(
#             status=Category.Status.PENDING
#         ).count()
#         return super().index(request, extra_context)
#
# admin_site = CustomAdminSite(name='custom_admin')