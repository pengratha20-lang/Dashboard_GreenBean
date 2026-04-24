"""
Integrations package for external services (Telegram, Email, etc.)
"""

from .telegram_service import get_telegram_notifier

__all__ = ['get_telegram_notifier']
