#!/usr/bin/env python
"""
Django command to run Telegram bot.
Usage: python manage.py run_telegram_bot
"""

import os
import asyncio
import django
from django.core.management.base import BaseCommand
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.telegram_bot_example import main


class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write('Starting Telegram bot...')
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Bot stopped by user'))
