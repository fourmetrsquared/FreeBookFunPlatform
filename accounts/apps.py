from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    name = 'accounts'
    verbose_name = _('User Accounts')
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """
        Import signal handlers when app is ready.
        
        Note: Use try/except to handle cases where Django isn't fully configured
        """
        try:
            # Only import signals when Django is fully configured
            import accounts.signals  # noqa
        except Exception as e:
            # Log the error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not import signals: {e}")
