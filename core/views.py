"""
Home view for the MD Books Library.

This module defines the main landing page view that displays featured books,
popular categories, trending tags, and recent activity to engage visitors.

Classes:
    HomeView - Main landing page with featured content

Features:
    - Featured books (most popular or editor's picks)
    - Recently added books
    - Popular categories with book counts
    - Trending tags
    - Recent reviews
    - Site statistics (total books, authors, reviews)

TODO: Add the following features in future iterations:
    - Search functionality on home page
    - User dashboard (if authenticated)
    - Reading recommendations based on user history
    - Featured authors spotlight
    - Book of the week/month
"""

from django.core.cache import cache
from django.db.models import Count, Avg, Q
from django.shortcuts import render
from django.views import View

from books.models import Book, Category, Tag, Review


class HomeView(View):
    """
    Main landing page for the MD Books Library.

    Displays featured content to engage visitors and showcase the library's offerings.
    Optimizes queries to load all necessary data efficiently.

    Context:
        featured_books: QuerySet[Book] - Popular or featured books (max 8)
        recent_books: QuerySet[Book] - Recently added books (max 8)
        popular_categories: QuerySet[Category] - Top categories by book count (max 10)
        trending_tags: QuerySet[Tag] - Most used tags (max 20)
        recent_reviews: QuerySet[Review] - Latest reviews (max 5)
        stats: dict - Site statistics (total books, authors, reviews, etc.)

    Features:
        - Query optimization via select_related() and prefetch_related()
        - Caching for expensive queries (popular categories, tags)
        - Responsive design support (Bootstrap grid)
        - SEO-friendly meta tags

    Performance:
        - Uses database-level aggregation for counts
        - Caches popular content for 1 hour
        - Minimizes N+1 queries with proper joins

    Example:
        GET /
        → Renders core/home.html with featured content
    """

    template_name = 'core/home.html'

    def get(self, request):
        """
        Handle GET request for the home page.

        Fetches all necessary data and renders the home template.

        Args:
            request (HttpRequest): The HTTP request object

        Returns:
            HttpResponse: Rendered home page with context data
        """
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def get_context_data(self, request):
        """
        Build the context dictionary for the home page template.

        Fetches and optimizes all data needed for the landing page.

        Args:
            request (HttpRequest): The HTTP request object

        Returns:
            dict: Context dictionary with all home page data
        """
        context = {}

        # Featured books (most viewed or highest rated)
        # TODO: Add "editor's picks" or "featured" field to Book model
        context['featured_books'] = self._get_featured_books()

        # Recently added books
        context['recent_books'] = self._get_recent_books()

        # Popular categories
        context['popular_categories'] = self._get_popular_categories()

        # Trending tags
        context['trending_tags'] = self._get_trending_tags()

        # Recent reviews
        context['recent_reviews'] = self._get_recent_reviews()

        # Site statistics
        context['stats'] = self._get_site_statistics()

        # TODO: Add user-specific content if authenticated
        # if request.user.is_authenticated:
        #     context['user_recommendations'] = self._get_user_recommendations(request.user)
        #     context['continue_reading'] = self._get_continue_reading(request.user)

        return context

    def _get_featured_books(self, limit=8):
        """
        Get featured books for the home page.

        Prioritizes books with high views and good ratings.

        Args:
            limit (int): Maximum number of books to return

        Returns:
            QuerySet: Featured published books

        TODO: Add "is_featured" boolean field to Book model
        TODO: Implement "book of the week" logic
        """
        return Book.objects.filter(
            is_published=True
        ).select_related(
            'author', 'category'
        ).prefetch_related(
            'tags'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).order_by(
            '-views', '-avg_rating', '-created_at'
        )[:limit]

    def _get_recent_books(self, limit=8):
        """
        Get recently added books.

        Args:
            limit (int): Maximum number of books to return

        Returns:
            QuerySet: Recently published books
        """
        return Book.objects.filter(
            is_published=True
        ).select_related(
            'author', 'category'
        ).prefetch_related(
            'tags'
        ).order_by('-created_at')[:limit]

    def _get_popular_categories(self, limit=10):
        """
        Get popular categories by book count.

        Uses caching to improve performance (categories change rarely).

        Args:
            limit (int): Maximum number of categories to return

        Returns:
            QuerySet: Top categories with book counts

        TODO: Implement cache invalidation when categories change
        """
        # Try to get from cache first
        cache_key = 'home_popular_categories'
        categories = cache.get(cache_key)

        if categories is None:
            # Cache miss - fetch from database
            categories = Category.objects.filter(
                status=Category.Status.APPROVED
            ).annotate(
                book_count=Count(
                    'books',
                    filter=Q(books__is_published=True)
                )
            ).filter(
                book_count__gt=0
            ).order_by('-book_count')[:limit]

            # Cache for 1 hour
            cache.set(cache_key, categories, 60 * 60)

        return categories

    def _get_trending_tags(self, limit=20):
        """
        Get trending tags by usage count.

        Args:
            limit (int): Maximum number of tags to return

        Returns:
            QuerySet: Top tags with book counts

        TODO: Implement cache for tags
        TODO: Add "trending" algorithm based on recent usage
        """
        return Tag.objects.annotate(
            book_count=Count(
                'books',
                filter=Q(books__is_published=True)
            )
        ).filter(
            book_count__gt=0
        ).order_by('-book_count')[:limit]

    def _get_recent_reviews(self, limit=5):
        """
        Get recent reviews with high ratings.

        Args:
            limit (int): Maximum number of reviews to return

        Returns:
            QuerySet: Recent positive reviews
        """
        return Review.objects.filter(
            rating__gte=4  # Only show positive reviews (4-5 stars)
        ).select_related(
            'book', 'author'
        ).order_by('-created_at')[:limit]

    def _get_site_statistics(self):
        """
        Calculate site-wide statistics.

        Returns:
            dict: Statistics dictionary with counts

        Example:
            {
                'total_books': 150,
                'total_authors': 45,
                'total_reviews': 320,
                'total_categories': 12,
                'total_tags': 85,
                'average_rating': 4.2,
            }
        """
        # TODO: Cache these statistics (update periodically, not on every request)
        stats = {
            'total_books': Book.objects.filter(is_published=True).count(),
            'total_authors': Book.objects.filter(
                is_published=True
            ).values('author').distinct().count(),
            'total_reviews': Review.objects.count(),
            'total_categories': Category.objects.filter(
                status=Category.Status.APPROVED
            ).count(),
            'total_tags': Tag.objects.count(),
            'average_rating': Review.objects.aggregate(
                avg=Avg('rating')
            )['avg'] or 0.0,
        }

        # Round average rating to 1 decimal place
        stats['average_rating'] = round(stats['average_rating'], 1)

        return stats

    # TODO: Implement user-specific recommendations
    # def _get_user_recommendations(self, user, limit=5):
    #     """
    #     Get personalized book recommendations for the user.
    #     
    #     Based on:
    #         - User's reading history
    #         - User's favorite categories/tags
    #         - Books similar to what user has read
    #     
    #     Args:
    #         user (User): The authenticated user
    #         limit (int): Maximum number of recommendations
    #     
    #     Returns:
    #         QuerySet: Recommended books
    #     """
    #     # TODO: Implement recommendation algorithm
    #     # 1. Get user's most-read categories
    #     # 2. Get user's favorite tags
    #     # 3. Find books matching those preferences
    #     # 4. Exclude books user has already read
    #     pass

    # TODO: Implement "continue reading" feature
    # def _get_continue_reading(self, user, limit=3):
    #     """
    #     Get books the user is currently reading.
    #     
    #     Args:
    #         user (User): The authenticated user
    #         limit (int): Maximum number of books
    #     
    #     Returns:
    #         QuerySet: Books user is currently reading
    #     """
    #     # TODO: Implement reading progress tracking
    #     # Need ReadingProgress model to track which chapters user has read
    #     pass

# ============================================
# Alternative: TemplateView Approach
# ============================================

# TODO: Consider using TemplateView for simpler implementation
# from django.views.generic import TemplateView
#
# class HomeView(TemplateView):
#     """
#     Simpler home view using TemplateView.
#     
#     TemplateView automatically handles GET requests and template rendering.
#     Override get_context_data() to add custom context.
#     """
#     template_name = 'core/home.html'
#     
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         
#         # Add your context data here
#         context['featured_books'] = Book.objects.filter(
#             is_published=True
#         ).order_by('-views')[:8]
#         
#         return context
