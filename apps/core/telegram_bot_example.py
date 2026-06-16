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

    def get_tags(self) -> list:
        """Fetch all active tags from backend."""
        try:
            response = requests.get(f'{self.api_base}/tags/')
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data.get('results', [])
                return data
            return []
        except Exception as e:
            logger.error(f"Error fetching tags: {e}")
            return []

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

    def get_category_businesses(self, category_id: int, tag_id: int = None) -> list:
        """Fetch businesses for a category, optionally filtered by tag."""
        try:
            url = f'{self.api_base}/categories/{category_id}/businesses/'
            if tag_id:
                url += f'?tag_id={tag_id}'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data.get('results', [])
                return data
            return []
        except Exception as e:
            logger.error(f"Error fetching businesses: {e}")
            return []

    def get_business(self, business_id: int) -> dict | None:
        """Fetch a single business by ID."""
        try:
            response = requests.get(f'{self.api_base}/businesses/{business_id}/')
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching business: {e}")
            return None

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


def category_label(cat: dict, flag_prefix: str = "") -> str:
    name = cat['name']
    if cat.get('show_flag', True):
        if flag_prefix:
            name = f"{flag_prefix}{name}"
        if name and ord(name[0]) >= 128:
            return name
        emoji = "📂" if cat.get('children') else "📁"
        return f"{emoji} {name}"
    return name


def build_tags_keyboard(tags: list) -> InlineKeyboardMarkup:
    keyboard = []
    row = []
    for tag in tags:
        label = f"{tag.get('flag_unicode', '') or '🏷️'} {tag['name']}".strip()
        row.append(InlineKeyboardButton(label, callback_data=f"tag_{tag['id']}"))
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def build_category_keyboard(categories: list, parent_id: int = None, inline: bool = False, flag_prefix: str = "", back_text: str = "🔙 Back", main_menu_text: str = "🏠 Main menu") -> InlineKeyboardMarkup:
    """Build inline keyboard for a list of categories."""
    keyboard = []
    if inline:
        row = []
        for i, cat in enumerate(categories):
            row.append(InlineKeyboardButton(category_label(cat, flag_prefix), callback_data=f"cat_{cat['id']}"))
            if len(row) == 2 or i == len(categories) - 1:
                keyboard.append(row)
                row = []
    else:
        for cat in categories:
            keyboard.append([
                InlineKeyboardButton(category_label(cat, flag_prefix), callback_data=f"cat_{cat['id']}")
            ])
    nav = []
    if parent_id is not None:
        nav.append(InlineKeyboardButton(back_text, callback_data=f"back_{parent_id}"))
    nav.append(InlineKeyboardButton(main_menu_text, callback_data="main_menu"))
    if nav:
        keyboard.append(nav)
    return InlineKeyboardMarkup(keyboard)


def build_content_keyboard(contents: list, parent_id: int, back_text: str = "🔙 Back", main_menu_text: str = "🏠 Main menu") -> InlineKeyboardMarkup:
    """Build inline keyboard for a list of content items."""
    keyboard = []
    for c in contents[:10]:
        keyboard.append([
            InlineKeyboardButton(f"📄 {c['title']}", callback_data=f"content_{c['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton(back_text, callback_data=f"back_{parent_id}"),
        InlineKeyboardButton(main_menu_text, callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    bot_handler.load_bot_settings()
    bt = bot_handler.bot_settings
    back_text = bt.back_button_text if bt else "🔙 Back"
    main_menu_text = bt.main_menu_button_text if bt else "🏠 Main menu"
    tags_prompt = bt.tags_prompt_text if bt else "🌍 Choose a country:"
    bot_user = await bot_handler.track_user(user.id, user.username)
    has_access = bot_handler.check_access(user.id)

    if not has_access:
        message = bot_handler.bot_settings.unauthorized_welcome_message if bot_handler.bot_settings else "Access denied."
        await update.message.reply_text(message)
        return

    message = bot_handler.bot_settings.authorized_welcome_message if bot_handler.bot_settings else "Welcome to the bot!"
    
    welcome_image = bot_handler.bot_settings.welcome_image if bot_handler.bot_settings else None
    if welcome_image:
        try:
            full_url = f"https://kids-genius.run.place{welcome_image.url}"
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=full_url
            )
        except Exception as e:
            logger.error(f"Error sending welcome image: {e}")
    
    await update.message.reply_text(message)

    context.user_data.pop('selected_tag', None)
    tags = bot_handler.get_tags()
    if tags:
        await update.message.reply_text(
            tags_prompt,
            reply_markup=build_tags_keyboard(tags)
        )
    else:
        bt = bot_handler.bot_settings
        cta = bt.root_cta_message if bt else "Choose category:"
        categories = bot_handler.get_categories()
        if categories:
            await update.message.reply_text(
                cta,
                reply_markup=build_category_keyboard(
                    categories, inline=True,
                    back_text=back_text, main_menu_text=main_menu_text
                )
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
    bot_handler.load_bot_settings()
    bt = bot_handler.bot_settings
    back_text = bt.back_button_text if bt else "🔙 Back"
    main_menu_text = bt.main_menu_button_text if bt else "🏠 Main menu"
    tags_prompt = bt.tags_prompt_text if bt else "🌍 Choose a country:"
    tags = bot_handler.get_tags()
    if tags:
        context.user_data.pop('selected_tag', None)
        await update.message.reply_text(
            tags_prompt,
            reply_markup=build_tags_keyboard(tags)
        )
    else:
        categories = bot_handler.get_categories()
        if categories:
            cta = bot_handler.bot_settings.root_cta_message if bot_handler.bot_settings else "Choose category:"
            await update.message.reply_text(
                cta,
                reply_markup=build_category_keyboard(
                    categories, inline=True,
                    back_text=back_text, main_menu_text=main_menu_text
                )
            )
        else:
            await update.message.reply_text("No categories available.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries."""
    query = update.callback_query
    data = query.data
    await query.answer()

    bot_handler.load_bot_settings()
    bt = bot_handler.bot_settings
    back_text = bt.back_button_text if bt else "🔙 Back"
    main_menu_text = bt.main_menu_button_text if bt else "🏠 Main menu"
    tags_prompt = bt.tags_prompt_text if bt else "🌍 Choose a country:"

    if data == "main_menu":
        context.user_data.pop('selected_tag', None)
        tags = bot_handler.get_tags()
        if tags:
            await query.edit_message_text(
                tags_prompt,
                reply_markup=build_tags_keyboard(tags)
            )
        else:
            await query.edit_message_text("No tags configured.")
        return

    if data.startswith("tag_"):
        tag_id = int(data.split("_")[1])
        all_tags = bot_handler.get_tags()
        selected_tag = next((t for t in all_tags if t['id'] == tag_id), None)
        if not selected_tag:
            await query.edit_message_text("Tag not found.")
            return

        context.user_data['selected_tag'] = selected_tag
        categories = bot_handler.get_categories()
        flag_prefix = ""
        if bot_handler.bot_settings and bot_handler.bot_settings.show_tag_flag_on_categories:
            flag_prefix = selected_tag.get('flag_unicode', '')

        if categories:
            cta = flag_prefix + " " + selected_tag['name']
            await query.edit_message_text(
                cta.strip(),
                reply_markup=build_category_keyboard(categories, inline=True, flag_prefix=flag_prefix, back_text=back_text, main_menu_text=main_menu_text)
            )
        else:
            await query.edit_message_text("No categories available.")
        return

    flag_prefix = ""
    if bot_handler.bot_settings and bot_handler.bot_settings.show_tag_flag_on_categories:
        selected_tag = context.user_data.get('selected_tag')
        if selected_tag:
            flag_prefix = selected_tag.get('flag_unicode', '')

    if data.startswith("cat_"):
        category_id = int(data.split("_")[1])
        category = bot_handler.get_category(category_id)
        if not category:
            await query.edit_message_text("Category not found.")
            return

        children = category.get('children', [])
        contents_data = bot_handler.get_category_contents(category_id)
        selected_tag = context.user_data.get('selected_tag')
        tag_id = selected_tag['id'] if selected_tag else None
        businesses_data = bot_handler.get_category_businesses(category_id, tag_id=tag_id)
        expand = category.get('expand_children_inline', True)

        if children:
            inline = category.get('inline_display', False)

            if expand:
                current_markup = query.message.reply_markup
                base_rows = list(current_markup.inline_keyboard) if current_markup else []

                nav_row = base_rows.pop() if base_rows and len(base_rows) > 0 else []

                child_rows = []
                if inline:
                    row = []
                    for child in children:
                        row.append(InlineKeyboardButton(category_label(child, flag_prefix), callback_data=f"cat_{child['id']}"))
                    if row:
                        child_rows.append(row)
                else:
                    for child in children:
                        child_rows.append([InlineKeyboardButton(category_label(child, flag_prefix), callback_data=f"cat_{child['id']}")])

                all_rows = base_rows + child_rows + ([nav_row] if nav_row else [])
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(all_rows))
            else:
                cta = category.get('cta_message', '').strip() or f"📂 **{category['name']}**"
                await query.message.reply_text(
                    cta,
                    reply_markup=build_category_keyboard(children, parent_id=category.get('parent'), inline=inline, flag_prefix=flag_prefix, back_text=back_text, main_menu_text=main_menu_text),
                    parse_mode='Markdown'
                )
        elif contents_data or businesses_data:
            name = category.get('cta_message', '').strip() or f"**{category['name']}**"
            keyboard = []
            for c in contents_data[:10]:
                keyboard.append([InlineKeyboardButton(f"📄 {c['title']}", callback_data=f"content_{c['id']}")])
            for b in businesses_data[:10]:
                keyboard.append([InlineKeyboardButton(f"{b.get('emoji', '🎁')} {b['title']}", callback_data=f"biz_{b['id']}_{category_id}")])
            keyboard.append([
                InlineKeyboardButton(back_text, callback_data=f"back_{category.get('parent') or 'None'}"),
                InlineKeyboardButton(main_menu_text, callback_data="main_menu")
            ])
            await query.edit_message_text(name, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            cta = category.get('cta_message', '').strip() or f"📂 **{category['name']}**\n\nNo items yet."
            keyboard = [[
                InlineKeyboardButton(back_text, callback_data=f"back_{category.get('parent') or 'None'}"),
                InlineKeyboardButton(main_menu_text, callback_data="main_menu")
            ]]
            await query.edit_message_text(cta, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return

    if data.startswith("back_main"):
        tags = bot_handler.get_tags()
        if tags:
            context.user_data.pop('selected_tag', None)
            await query.edit_message_text(
                tags_prompt,
                reply_markup=build_tags_keyboard(tags)
            )
        return

    if data.startswith("back_"):
        parent_id = data.split("_")[1]
        if parent_id == "None":
            tags = bot_handler.get_tags()
            if tags:
                context.user_data.pop('selected_tag', None)
                await query.edit_message_text(
                    tags_prompt,
                    reply_markup=build_tags_keyboard(tags)
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
            reply_markup=build_category_keyboard(active_children, parent_id=parent.get('parent'), inline=inline, flag_prefix=flag_prefix, back_text=back_text, main_menu_text=main_menu_text),
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
                InlineKeyboardButton(back_text, callback_data=f"cat_{cat_id}"),
                InlineKeyboardButton(main_menu_text, callback_data="main_menu")
            ]
        ]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    if data.startswith("biz_"):
        parts = data.split("_")
        biz_id = int(parts[1])
        cat_id = int(parts[2]) if len(parts) > 2 else None
        business = bot_handler.get_business(biz_id)
        if not business:
            await query.edit_message_text("Business not found.")
            return

        lines = [f"🏪 **{business['title']}**"]
        truncated = False
        if business.get('description'):
            desc = business['description']
            truncated = len(desc) > 200
            if truncated:
                desc = desc[:200]
            lines.append(f"\n_{desc}_")
            if truncated:
                lines.append(f"\n... 📖")

        if business.get('address'):
            lines.append(f"\n📍 {business['address']}")
        if business.get('hotline'):
            lines.append(f"📞 {business['hotline']}")
        if business.get('online_store'):
            lines.append(f"🛒 [Online Store]({business['online_store']})")
        if business.get('facebook'):
            lines.append(f"📘 [Facebook]({business['facebook']})")
        if business.get('instagram'):
            lines.append(f"📸 [Instagram]({business['instagram']})")
        if business.get('tiktok'):
            lines.append(f"🎵 [TikTok]({business['tiktok']})")
        if business.get('youtube'):
            lines.append(f"🎬 [YouTube]({business['youtube']})")

        message = "\n".join(lines)
        keyboard = []
        if truncated:
            keyboard.append([InlineKeyboardButton("📖 Read full description", callback_data=f"desc_{biz_id}")])
        keyboard.append([
            InlineKeyboardButton(back_text, callback_data=f"cat_{cat_id}"),
            InlineKeyboardButton(main_menu_text, callback_data="main_menu")
        ])

        logo = business.get('logo')
        if logo:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=logo
            )
        await query.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    if data.startswith("desc_"):
        biz_id = int(data.split("_")[1])
        business = bot_handler.get_business(biz_id)
        if business and business.get('description'):
            await query.message.reply_text(
                f"📖 **{business['title']}**\n\n{business['description']}",
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

    application.add_handler(CallbackQueryHandler(handle_callback, pattern=r'^(tag_|cat_|content_|back_main|back_|main_menu|rate_|biz_|desc_)'))

    application.run_polling()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
