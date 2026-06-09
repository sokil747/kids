import os
import requests
import logging
from typing import Optional
from decouple import config
from asgiref.sync import sync_to_async
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
        self.api_base = config('API_BASE_URL', default='http://localhost:8000/api')
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

    async def track_user(self, user_id: int, username: str = None, platform: str = 'telegram'):
        """Track or create user in database."""
        try:
            user, created = await sync_to_async(BotUser.objects.get_or_create)(
                user_id=str(user_id),
                platform=platform,
                defaults={'username': username}
            )
            await sync_to_async(user.increment_interaction)()
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
        """Fetch top-level categories from backend."""
        try:
            response = requests.get(f'{self.api_base}/categories/')
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data.get('results', [])
                return data
            return []
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []

    def get_category(self, category_id: int) -> dict:
        """Fetch a single category with children."""
        try:
            response = requests.get(f'{self.api_base}/categories/{category_id}/')
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching category {category_id}: {e}")
            return {}

    def get_category_contents(self, category_id: int) -> list:
        """Fetch contents for category."""
        try:
            response = requests.get(
                f'{self.api_base}/categories/{category_id}/contents/'
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data.get('results', [])
                return data
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


def build_category_keyboard(categories: list, parent_id: int = None, inline: bool = False) -> InlineKeyboardMarkup:
    """Build inline keyboard for a list of categories."""
    keyboard = []
    if inline:
        row = []
        for cat in categories:
            emoji = "📂" if cat.get('children') else "📁"
            row.append(InlineKeyboardButton(f"{emoji} {cat['name']}", callback_data=f"cat_{cat['id']}"))
        if row:
            keyboard.append(row)
    else:
        for cat in categories:
            emoji = "📂" if cat.get('children') else "📁"
            keyboard.append([
                InlineKeyboardButton(f"{emoji} {cat['name']}", callback_data=f"cat_{cat['id']}")
            ])
    nav = []
    if parent_id is not None:
        nav.append(InlineKeyboardButton("🔙 Back", callback_data=f"back_{parent_id}"))
    nav.append(InlineKeyboardButton("🏠 Main menu", callback_data="main_menu"))
    if nav:
        keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)


def build_content_keyboard(contents: list, parent_id: int) -> InlineKeyboardMarkup:
    """Build inline keyboard for a list of content items."""
    keyboard = []
    for c in contents[:10]:
        keyboard.append([
            InlineKeyboardButton(f"📄 {c['title']}", callback_data=f"content_{c['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data=f"back_{parent_id}"),
        InlineKeyboardButton("🏠 Main menu", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    bot_user = await bot_handler.track_user(user.id, user.username)
    has_access = bot_handler.check_access(user.id)

    if not has_access:
        message = bot_handler.bot_settings.unauthorized_welcome_message if bot_handler.bot_settings else "Access denied."
        await update.message.reply_text(message)
        return

    message = bot_handler.bot_settings.authorized_welcome_message if bot_handler.bot_settings else "Welcome to the bot!"
    await update.message.reply_text(message)

    categories = bot_handler.get_categories()
    if categories:
        cta = bot_handler.bot_settings.root_cta_message if bot_handler.bot_settings else "Choose category:"
        await update.message.reply_text(
            cta,
            reply_markup=build_category_keyboard(categories, inline=True)
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
    categories = bot_handler.get_categories()
    if categories:
        cta = bot_handler.bot_settings.root_cta_message if bot_handler.bot_settings else "Choose category:"
        await update.message.reply_text(
            cta,
            reply_markup=build_category_keyboard(categories, inline=True)
        )
    else:
        await update.message.reply_text("No categories available.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries."""
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "main_menu":
        categories = bot_handler.get_categories()
        if categories:
            cta = bot_handler.bot_settings.root_cta_message if bot_handler.bot_settings else "Choose category:"
            await query.edit_message_text(
                cta,
                reply_markup=build_category_keyboard(categories, inline=True)
            )
        else:
            await query.edit_message_text("No categories available.")
        return

    if data.startswith("cat_"):
        category_id = int(data.split("_")[1])
        category = bot_handler.get_category(category_id)
        if not category:
            await query.edit_message_text("Category not found.")
            return

        children = category.get('children', [])
        contents_data = bot_handler.get_category_contents(category_id)

        if children:
            parent_id = category.get('parent')
            inline = category.get('inline_display', False)
            cta = category.get('cta_message', '').strip() or f"📂 **{category['name']}**"
            await query.edit_message_text(
                cta,
                reply_markup=build_category_keyboard(children, parent_id=parent_id, inline=inline),
                parse_mode='Markdown'
            )
        elif contents_data:
            await query.edit_message_text(
                f"📖 Content in **{category['name']}**:",
                reply_markup=build_content_keyboard(contents_data, parent_id=category_id),
                parse_mode='Markdown'
            )
        else:
            cta = category.get('cta_message', '').strip() or f"📂 **{category['name']}**\n\nNo subcategories or content yet."
            await query.edit_message_text(
                cta,
                parse_mode='Markdown'
            )
        return

    if data.startswith("back_"):
        parent_id = data.split("_")[1]
        if parent_id == "None":
            categories = bot_handler.get_categories()
            if categories:
                await query.edit_message_text(
                    "📚 Main menu — select a category:",
                    reply_markup=build_category_keyboard(categories, inline=True)
                )
            return

        parent = bot_handler.get_category(int(parent_id))
        if not parent:
            await query.edit_message_text("Category not found.")
            return

        children = parent.get('children', [])
        active_children = [c for c in children if c.get('is_active', True)]
        inline = parent.get('inline_display', False)
        cta = parent.get('cta_message', '').strip() or f"📂 **{parent['name']}**"
        await query.edit_message_text(
            cta,
            reply_markup=build_category_keyboard(active_children, parent_id=parent.get('parent'), inline=inline),
            parse_mode='Markdown'
        )
        return

    if data.startswith("content_"):
        parts = data.split("_")
        content_id = int(parts[1])
        content = bot_handler.get_content_detail(content_id)

        if not content:
            await query.edit_message_text("Content not found.")
            return

        message = f"""
📙 **{content['title']}**

{content.get('description', '')}

{content.get('body', '')[:500]}

⭐ Rating: {content.get('average_rating', 'Not rated')}  |  👁️ Views: {content.get('views_count', 0)}
"""
        cat_id = content.get('category')
        keyboard = [
            [
                InlineKeyboardButton("⭐ 5", callback_data=f"rate_{content_id}_5"),
                InlineKeyboardButton("👍 4", callback_data=f"rate_{content_id}_4"),
                InlineKeyboardButton("👌 3", callback_data=f"rate_{content_id}_3"),
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data=f"back_{cat_id}"),
                InlineKeyboardButton("🏠 Main menu", callback_data="main_menu")
            ]
        ]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    if data.startswith("rate_"):
        parts = data.split("_")
        content_id = int(parts[1])
        rating = int(parts[2])
        user = update.effective_user

        success = bot_handler.rate_content(content_id, user.id, rating)
        if success:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ Thanks for rating! ({rating}★)")
        else:
            await query.message.reply_text("❌ Failed to save rating.")
        return


def main() -> None:
    """Start the bot."""
    if not bot_handler.bot_settings:
        logger.error("Bot settings not configured")
        return

    application = Application.builder().token(
        bot_handler.bot_settings.telegram_token
    ).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", categories_command))

    application.add_handler(CallbackQueryHandler(handle_callback, pattern=r'^(cat_|content_|back_|main_menu|rate_)'))

    application.run_polling()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
