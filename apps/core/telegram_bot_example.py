"""
Example Telegram bot handler.
Shows how to integrate the Django backend with python-telegram-bot.
This is a starting point for your bot implementation.
"""

import os
import requests
import logging
from typing import Optional
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apps.core.models import BotSettings
from apps.access_control.models import BotUser

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """
    Telegram bot handler for ContentMentor.
    Connect Django backend with Telegram bot.
    """

    def __init__(self):
        self.api_base = os.getenv('API_BASE_URL', 'http://localhost:8000/api')
        self.bot_settings: Optional[BotSettings] = None
        self.load_bot_settings()

    def load_bot_settings(self):
        """Load bot settings from database."""
        try:
            self.bot_settings = BotSettings.objects.filter(
                is_active=True
            ).first()
            if not self.bot_settings:
                logger.error("No active bot settings found")
        except Exception as e:
            logger.error(f"Error loading bot settings: {e}")

    def track_user(self, user_id: int, username: str = None, platform: str = 'telegram'):
        """Track or create user in database."""
        try:
            user, created = BotUser.objects.get_or_create(
                user_id=str(user_id),
                platform=platform,
                defaults={'username': username}
            )
            user.increment_interaction()
            return user
        except Exception as e:
            logger.error(f"Error tracking user {user_id}: {e}")

    def check_access(self, user_id: int) -> bool:
        """Check if user has access to bot."""
        try:
            if not self.bot_settings:
                return False
            
            response = requests.get(
                f'{self.api_base}/check-access/{user_id}/{self.bot_settings.access_mode}/'
            )
            return response.json().get('has_access', False)
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            return False

    def get_categories(self) -> list:
        """Fetch main categories from backend."""
        try:
            response = requests.get(f'{self.api_base}/categories/')
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []

    def get_category_contents(self, category_id: int) -> list:
        """Fetch contents for category."""
        try:
            response = requests.get(
                f'{self.api_base}/categories/{category_id}/contents/'
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching contents: {e}")
            return []

    def get_content_detail(self, content_id: int) -> dict:
        """Fetch content details."""
        try:
            response = requests.get(f'{self.api_base}/content/{content_id}/')
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
            return {}

    def rate_content(self, content_id: int, user_id: int, rating: int, comment: str = ''):
        """Submit rating for content."""
        try:
            response = requests.post(
                f'{self.api_base}/content/{content_id}/rate/',
                json={
                    'user_id': str(user_id),
                    'rating': rating,
                    'comment': comment
                }
            )
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Error rating content: {e}")
            return False


# Initialize bot handler
bot_handler = TelegramBotHandler()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    
    # Track user
    bot_user = bot_handler.track_user(user.id, user.username)
    
    # Check access
    has_access = bot_handler.check_access(user.id)
    
    # Send appropriate welcome message
    if not has_access:
        # Unauthorized message
        message = bot_handler.bot_settings.unauthorized_welcome_message if bot_handler.bot_settings else "Access denied."
        await update.message.reply_text(message)
        return
    
    # Authorized message with categories
    message = bot_handler.bot_settings.authorized_welcome_message if bot_handler.bot_settings else "Welcome to the bot!"
    await update.message.reply_text(
        message,
        reply_markup=get_categories_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
🆘 **Available Commands:**

/start - Start the bot
/help - Show this help message
/categories - Browse categories
/profile - View your profile
/status - Check bot status

**Features:**
• Browse educational content
• Rate content
• Access premium materials
• Track your learning progress
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of categories."""
    await update.message.reply_text(
        "📚 Select a category:",
        reply_markup=get_categories_keyboard()
    )


def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with categories."""
    categories = bot_handler.get_categories()
    
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {category['name']}",
                callback_data=f"cat_{category['id']}"
            )
        ])
    
    return InlineKeyboardMarkup(keyboard)


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle category selection."""
    query = update.callback_query
    category_id = int(query.data.split('_')[1])
    
    await query.answer()
    
    contents = bot_handler.get_category_contents(category_id)
    
    if not contents:
        await query.edit_message_text("No content available in this category.")
        return
    
    keyboard = []
    for content in contents[:10]:  # Limit to 10 items
        keyboard.append([
            InlineKeyboardButton(
                f"📄 {content['title']}",
                callback_data=f"content_{content['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data="back_categories")
    ])
    
    await query.edit_message_text(
        "📖 Select content:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def content_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle content selection."""
    query = update.callback_query
    content_id = int(query.data.split('_')[1])
    
    await query.answer()
    
    content = bot_handler.get_content_detail(content_id)
    
    if not content:
        await query.edit_message_text("Content not found.")
        return
    
    message = f"""
📙 **{content['title']}**

{content['description']}

**Content:** {content['body'][:200]}...

⭐ Rating: {content.get('average_rating', 'Not rated')}
👁️ Views: {content.get('views_count', 0)}
"""
    
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data=f"rate_{content_id}_5"),
            InlineKeyboardButton("👍", callback_data=f"rate_{content_id}_4"),
            InlineKeyboardButton("👌", callback_data=f"rate_{content_id}_3"),
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_categories")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


def main() -> None:
    """Start the bot."""
    if not bot_handler.bot_settings:
        logger.error("Bot settings not configured")
        return
    
    # Create the Application
    application = Application.builder().token(
        bot_handler.bot_settings.telegram_token
    ).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", categories_command))
    
    application.add_handler(CallbackQueryHandler(category_callback, pattern=r'^cat_'))
    application.add_handler(CallbackQueryHandler(content_callback, pattern=r'^content_'))

    # Run the bot
    application.run_polling()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
