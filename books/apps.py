"""
Application configuration for the books app.

This module configures the books application for Django, including:
    - App metadata (name, verbose name)
    - Default auto field for primary keys
    - Signal registration
    - App initialization logic

The AppConfig class is automatically discovered by Django when the app
is included in INSTALLED_APPS.

Configuration:
    name: 'books' - The Python path to the application
    verbose_name: 'Books Library' - Human-readable name for admin
    default_auto_field: 'django.db.models.BigAutoField' - Primary key type

Signal Registration:
    The ready() method is called when Django starts and is used to
    import signal handlers. This ensures signals are connected before
    any models are accessed.

TODO: Add the following features in future iterations:
    - Custom app initialization logic
    - App-specific settings validation
    - Health check endpoints
    - Background task registration (Celery)
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BooksConfig(AppConfig):
    """
    Configuration class for the books application.

    This class is automatically instantiated by Django when the application
    is loaded. It provides metadata and initialization logic for the app.

    Attributes:
        name (str): The Python path to the application ('books')
        verbose_name (str): Human-readable name for the admin interface
        default_auto_field (str): The type of auto-created primary key field

    Methods:
        ready(): Called when Django starts - used to register signals

    Example:
        # In settings.py
        INSTALLED_APPS = [
            ...
            'books.apps.BooksConfig',  # or just 'books'
        ]

    Note:
        If you use just 'books' in INSTALLED_APPS, Django will automatically
        find this BooksConfig class. You can also explicitly specify the path:
        'books.apps.BooksConfig'
    """

    # The Python path to the application
    # This must match the directory name
    name = 'books'

    # Human-readable name for the admin interface
    # This appears in the admin index page
    # TODO: Wrap with gettext_lazy for internationalization
    verbose_name = _('Books Library')

    # Default auto field for primary keys (Django 3.2+)
    # BigAutoField creates 64-bit integers (supports up to 9 quintillion records)
    # This is the recommended default for new Django projects
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """
        Called when Django starts and the app is fully loaded.

        This method is used to:
            1. Import signal handlers to connect them
            2. Perform app-specific initialization
            3. Validate app configuration

        Important:
            - This method is called once when Django starts
            - Do NOT import models here (causes circular imports)
            - Import signals in a separate module and import that module here

        Example:
            def ready(self):
                # Import signal handlers
                import books.signals

                # Or import specific signals
                from . import signals

        TODO: Implement signal handlers for:
            - Post-save: Update book reading time when chapters change
            - Post-save: Update cached average rating when reviews change
            - Post-save: Clear cache when categories/tags change
            - Post-delete: Clean up related data
        """
        # TODO: Import signal handlers
        # This ensures signals are connected before any models are accessed
        # import books.signals

        # TODO: Perform app initialization
        # Example: Validate settings, register background tasks, etc.
        # self._validate_settings()
        # self._register_celery_tasks()

        # TODO: Add health check registration
        # if hasattr(self, 'health_checks'):
        #     register_health_checks(self.health_checks)

        pass

    # TODO: Add custom methods for app initialization
    # def _validate_settings(self):
    #     """
    #     Validate app-specific settings.
    #     
    #     Called during app initialization to ensure all required
    #     settings are present and valid.
    #     """
    #     from django.conf import settings
    #     
    #     # Example: Check for required settings
    #     if not hasattr(settings, 'BOOKS_MAX_UPLOAD_SIZE'):
    #         raise ImproperlyConfigured(
    #             'BOOKS_MAX_UPLOAD_SIZE setting is required.'
    #         )

    # TODO: Add Celery task registration
    # def _register_celery_tasks(self):
    #     """
    #     Register Celery tasks for background processing.
    #     
    #     This ensures tasks are available when Celery starts.
    #     """
    #     from celery import app as celery_app
    #     
    #     # Import tasks to register them
    #     from . import tasks

    # TODO: Add health checks
    # health_checks = [
    #     'books.health.DatabaseHealthCheck',
    #     'books.health.CacheHealthCheck',
    # ]

# ============================================
# Alternative: Simple Configuration
# ============================================

# If you don't need custom initialization, you can use a simpler approach:
# Just create an empty apps.py or omit it entirely.
# Django will automatically create a default AppConfig.

# However, it's recommended to always have an explicit AppConfig for:
# 1. Better control over app metadata
# 2. Signal registration
# 3. Future extensibility


# ============================================
# Signal Registration Pattern
# ============================================

# When you create signal handlers, follow this pattern:

# 1. Create books/signals.py:
# ```python
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# from .models import Book, Review
#
# @receiver(post_save, sender=Review)
# def update_book_rating(sender, instance, **kwargs):
#     """Update book's cached rating when a review is saved."""
#     # Update logic here
#     pass
# ```

# 2. Import signals in apps.py ready() method:
# ```python
# def ready(self):
#     import books.signals  # This connects all signals
# ```

# This ensures signals are connected before any models are accessed,
# preventing issues where signals aren't triggered on early model saves.


# ============================================
# App Initialization Best Practices
# ============================================

# DO:
# ✓ Import signals in ready()
# ✓ Validate settings in ready()
# ✓ Register background tasks in ready()
# ✓ Perform one-time initialization in ready()

# DON'T:
# ✗ Import models in ready() (causes circular imports)
# ✗ Perform database queries in ready() (database may not be ready)
# ✗ Import views or forms in ready() (not needed at startup)
# ✗ Do heavy computation in ready() (slows down Django startup)


# ============================================
# Testing the Configuration
# ============================================

# You can test that your AppConfig is working correctly:

# 1. Check that the app is loaded:
# ```python
# from django.apps import apps
# config = apps.get_app_config('books')
# print(config.verbose_name)  # Should print: Books Library
# ```

# 2. Check that signals are connected:
# ```python
# from django.db.models.signals import post_save
# from books.models import Review
# receivers = post_save._live_receivers(Review)
# print(len(receivers))  # Should show number of connected receivers
# ```

# 3. Run Django checks:
# ```bash
# python manage.py check
# ```