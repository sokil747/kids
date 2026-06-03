# ContentMentor - Django Bot Backend

A comprehensive Django application for managing content through Telegram and WhatsApp bots with hierarchical categories, access control, and admin panel.

## Features

### Core Features
- ✅ **Bot Settings Management** - Manage Telegram/WhatsApp bot credentials through admin panel
- ✅ **Hierarchical Content Categories** - Create unlimited nested category structure
- ✅ **Rich Content Management** - Support for text, images, videos, files, links, and quizzes
- ✅ **Flexible Access Control** - Public, Private, Paid, and Test modes
- ✅ **User Management** - Track bot users by Telegram/WhatsApp user ID
- ✅ **Subscription System** - Flexible subscription plans with expiration tracking
- ✅ **Content Ratings** - User feedback and ratings for content
- ✅ **Audit Logging** - Track all admin actions on bot configuration
- ✅ **REST API** - Full REST API for bot integration

### Bot Modes
- **Public** - Anyone can access all content
- **Private** - Only whitelisted users have access (by Telegram user ID)
- **Paid** - Premium subscribers only
- **Test** - Limited testing mode for development

## Project Structure

```
content_mentor/
├── config/                 # Django configuration
│   ├── settings.py        # Main settings file
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI application
├── apps/
│   ├── core/             # Bot settings and audit logs
│   │   ├── models.py     # BotSettings, AuditLog
│   │   └── admin.py      # Admin interface
│   ├── content/          # Content and categories
│   │   ├── models.py     # Category, Content, ContentRating
│   │   ├── admin.py      # Admin interface with hierarchy support
│   │   ├── views.py      # REST API views
│   │   ├── serializers.py # DRF serializers
│   │   └── urls.py       # API routes
│   └── access_control/   # User access and subscriptions
│       ├── models.py     # BotUser, UserCategoryAccess, SubscriptionPlan, UserSubscription
│       ├── admin.py      # Admin interface
│       ├── views.py      # REST API views
│       ├── serializers.py # DRF serializers
│       └── urls.py       # API routes
├── templates/            # HTML templates
├── static/              # CSS, JS, images
└── manage.py            # Django management script
```

## Bot Information

- **Bot Username**: @kidsgenius_bot
- **Bot Token**: `<BOT_TOKEN_REMOVED>`
- **Platform**: Telegram (WhatsApp ready for future integration)
- **Access Mode**: Configurable (default: Public)

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- PostgreSQL or SQLite (default)

### 1. Clone and Setup Virtual Environment

```bash
cd /home/stranger27/projects/kids/content_mentor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin user
```

### 6. Load Initial Bot Settings

```bash
python manage.py shell
>>> from apps.core.models import BotSettings
>>> BotSettings.objects.create(
...     telegram_token='<BOT_TOKEN_REMOVED>',
...     telegram_nickname='kidsgenius_bot',
...     access_mode='public',
...     is_active=True,
...     description='KidsGenius - Educational content for children'
... )
>>> exit()
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Access admin panel at: `http://localhost:8000/admin`

## Admin Panel Usage

### Bot Settings Configuration
1. Go to **Admin > Bot Settings**
2. Configure Telegram token and nickname
3. Set access mode (Public, Private, Paid, Test)
4. Enable/disable bot status
5. Save changes (automatically applied to bot)

### Category Management
1. Go to **Admin > Categories**
2. Create parent categories first
3. Add subcategories by selecting parent
4. Set display order and featured status
5. Upload category icons/thumbnails

### Content Management
1. Go to **Admin > Contents**
2. Select category
3. Add title, description, and body
4. Choose content type (text, image, video, etc.)
5. Set premium/free access
6. Publish or save as draft

### User Access Control
1. Go to **Admin > Bot Users**
2. View all users interacting with bot
3. Whitelist users for private mode
4. Grant premium access with expiration dates
5. View interaction statistics

### Subscription Management
1. Create subscription plans with pricing
2. Assign plans to users manually or via payment API
3. Track subscription status and expiration
4. View subscription history

## REST API Endpoints

### Categories
```
GET    /api/categories/              # List all categories
GET    /api/categories/<id>/         # Get category detail
GET    /api/categories/<id>/contents/  # Get contents in category
```

### Content
```
GET    /api/content/                 # List all content
GET    /api/content/<id>/            # Get content detail
POST   /api/content/<id>/rate/       # Rate content
```

### User Access Control
```
GET    /api/check-access/<user_id>/<access_mode>/  # Check access
GET    /api/user/<user_id>/                        # Get user info
POST   /api/user/<user_id>/interact/               # Log interaction
```

### Subscription Plans
```
GET    /api/plans/                   # List subscription plans
GET    /api/plans/<id>/              # Get plan detail
```

## Example Bot Integration

```python
# Example: Check user access before sending content
import requests

user_id = "123456789"  # Telegram user ID
access_mode = "public"  # or "private", "paid", "test"

response = requests.get(
    f'http://localhost:8000/api/check-access/{user_id}/{access_mode}/'
)
access_data = response.json()

if access_data['has_access']:
    # Send content to user
    pass
else:
    # Send access denied message
    pass
```

## Database Schema Overview

### Core App
- **BotSettings** - Bot configuration and credentials
- **AuditLog** - Admin action tracking

### Content App
- **Category** - Hierarchical content categories
- **Content** - Individual content items
- **ContentRating** - User ratings and feedback

### Access Control App
- **BotUser** - Bot user profiles (by Telegram/WhatsApp ID)
- **UserCategoryAccess** - Fine-grained category-level access
- **SubscriptionPlan** - Available subscription tiers
- **UserSubscription** - User subscription history

## Configuration Options

### Access Modes
- **Public**: Anyone can access all non-premium content
- **Private**: Only whitelisted users (by Telegram ID) can access
- **Paid**: Premium subscribers only
- **Test**: For testing with whitelisted/premium users

### Content Types
- Text
- Image
- Video
- File
- Link
- Quiz

### Platform Support
- Telegram (active)
- WhatsApp (architecture ready for integration)

## Deployment

### For Production:
1. Set `DEBUG=False` in .env
2. Update `SECRET_KEY` to a secure random value
3. Use PostgreSQL database
4. Configure `ALLOWED_HOSTS`
5. Use environment variables for sensitive data
6. Set up HTTPS
7. Configure CORS appropriately

### Using Gunicorn:
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Using Docker:
See `Dockerfile` (to be created)

## Future Enhancements

- [ ] WhatsApp bot integration
- [ ] Payment gateway integration (Stripe, PayPal)
- [ ] Telegram bot webhook setup
- [ ] Analytics dashboard
- [ ] Content search and filtering
- [ ] Multi-language support
- [ ] Advanced user segmentation
- [ ] A/B testing for content
- [ ] Automated content scheduling
- [ ] Bot response templates

## Security Considerations

1. **Bot Token**: Keep tokens secure, never commit to git
2. **Admin Access**: Use strong passwords for superuser
3. **User IDs**: Validate user IDs from API requests
4. **Database**: Use strong passwords for database
5. **HTTPS**: Always use HTTPS in production
6. **CORS**: Configure appropriate CORS origins
7. **Rate Limiting**: Implement rate limiting on API endpoints

## Troubleshooting

### Bot not responding
- Check bot token in admin settings
- Verify `is_active` is True
- Check logs in `logs/django.log`

### Access issues
- Verify user is in whitelist for private mode
- Check subscription expiration date for paid mode
- Ensure bot access_mode matches request

### Database errors
- Run `python manage.py migrate`
- Check database connection settings in `.env`

## Support & Documentation

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Telegram Bot API: https://core.telegram.org/bots/api
- WhatsApp Business API: https://www.whatsapp.com/business/api/

## License

MIT License

## Contact

For issues or questions, contact the development team.
