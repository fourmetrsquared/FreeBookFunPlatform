"""
URL routing configuration for the core application.

This module defines URL patterns for the main landing page and other
core views that don't belong to a specific domain app (books, accounts, etc.).

URL Structure:
    /    → Home page (landing page with featured content)

Namespace: None (core URLs are typically at the root level)

Usage:
    This file is included in the main project's urls.py:

    # config/urls.py
    from django.urls import path, include

    urlpatterns = [
        path('', include('core.urls')),          # ← Core URLs at root
        path('books/', include('books.urls')),
        path('accounts/', include('accounts.urls')),
        path('admin/', admin.site.urls),
    ]

TODO: Add the following routes in future iterations:
    - /about/          → About page
    - /contact/        → Contact form
    - /terms/          → Terms of service
    - /privacy/        → Privacy policy
    - /faq/            → Frequently asked questions
    - /search/         → Global search results
    - /dashboard/      → User dashboard (authenticated)
    - /sitemap.xml     → SEO sitemap
    - /robots.txt      → Search engine crawling rules
"""

from django.urls import path
from .views import HomeView

# TODO: Import additional views as they are created
# from .views import (
#     HomeView,
#     AboutView,
#     ContactView,
#     TermsView,
#     PrivacyView,
#     FAQView,
#     SearchView,
#     DashboardView,
# )

# TODO: Consider adding app_name if core grows into a larger app
# app_name = 'core'

urlpatterns = [
    # ============================================
    # 🏠 HOME PAGE
    # ============================================

    # Main landing page with featured books, categories, and tags
    # URL: /
    # View: HomeView
    # Template: core/home.html
    # Access: Public (no authentication required)
    path(
        '',
        HomeView.as_view(),
        name='home'
    ),

    # ============================================
    # TODO: STATIC PAGES
    # ============================================

    # About page - information about the platform
    # URL: /about/
    # View: AboutView (TemplateView)
    # Template: core/about.html
    # path('about/', AboutView.as_view(), name='about'),

    # Contact form - allow users to send messages
    # URL: /contact/
    # View: ContactView (FormView)
    # Template: core/contact.html
    # path('contact/', ContactView.as_view(), name='contact'),

    # Terms of service
    # URL: /terms/
    # View: TermsView (TemplateView)
    # Template: core/terms.html
    # path('terms/', TermsView.as_view(), name='terms'),

    # Privacy policy
    # URL: /privacy/
    # View: PrivacyView (TemplateView)
    # Template: core/privacy.html
    # path('privacy/', PrivacyView.as_view(), name='privacy'),

    # Frequently asked questions
    # URL: /faq/
    # View: FAQView (TemplateView)
    # Template: core/faq.html
    # path('faq/', FAQView.as_view(), name='faq'),

    # ============================================
    # TODO: SEARCH & DISCOVERY
    # ============================================

    # Global search results page
    # URL: /search/?q=django
    # View: SearchView (ListView)
    # Template: core/search.html
    # path('search/', SearchView.as_view(), name='search'),

    # ============================================
    # TODO: USER DASHBOARD
    # ============================================

    # User dashboard (requires authentication)
    # URL: /dashboard/
    # View: DashboardView (TemplateView)
    # Template: core/dashboard.html
    # path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # ============================================
    # TODO: SEO & TECHNICAL ROUTES
    # ============================================

    # SEO sitemap for search engines
    # URL: /sitemap.xml
    # View: sitemap (from django.contrib.sitemaps)
    # from django.contrib.sitemaps.views import sitemap
    # from .sitemaps import BookSitemap, CategorySitemap
    # path('sitemap.xml', sitemap, {
    #     'sitemaps': {
    #         'books': BookSitemap,
    #         'categories': CategorySitemap,
    #     }
    # }, name='django.contrib.sitemaps.views.sitemap'),

    # Robots.txt for search engine crawling rules
    # URL: /robots.txt
    # View: RobotsView (TemplateView)
    # Template: core/robots.txt (content_type='text/plain')
    # path('robots.txt', RobotsView.as_view(), name='robots'),

    # Favicon (optional, can also be served via static files)
    # URL: /favicon.ico
    # from django.views.generic import RedirectView
    # path('favicon.ico', RedirectView.as_view(
    #     url='/static/images/favicon.ico', permanent=True
    # ), name='favicon'),
]