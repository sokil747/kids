"""
Django command to run Telegram bot.
Usage: python manage.py run_telegram_bot
"""

from django.core.management.base import BaseCommand
from apps.core.telegram_bot_example import main


class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write('Starting Telegram bot...')
        try:
            main()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Bot stopped by user'))
