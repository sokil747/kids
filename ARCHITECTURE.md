# ContentMentor - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   TELEGRAM / WHATSAPP BOTS                      │
│                  (python-telegram-bot, Twilio)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  REST API   │
                    │  Endpoints  │
                    └──────┬──────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   DJANGO APPLICATION                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Core App    │  │ Content App  │  │ Access Control App   │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────────────┤  │
│  │ • Bot        │  │ • Category   │  │ • Bot User           │  │
│  │   Settings   │  │ • Content    │  │ • User Category      │  │
│  │ • Audit Log  │  │ • Content    │  │   Access             │  │
│  │              │  │   Rating     │  │ • Subscription       │  │
│  │              │  │              │  │   Plan               │  │
│  │              │  │              │  │ • User Subscription  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                  │                     │               │
└─────────┼──────────────────┼─────────────────────┼───────────────┘
          │                  │                     │
┌─────────▼──────────────────▼─────────────────────▼───────────────┐
│                    DJANGO ORM / Models                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                DATABASE (SQLite / PostgreSQL)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### User Access Flow
```
┌──────────────────────┐
│  Telegram User       │
│  (user_id: 123)      │
└──────────┬───────────┘
           │
           │ /start command
           │
           ▼
┌──────────────────────────────────────────────┐
│  Check User Access                           │
│  GET /api/check-access/123/public/           │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Access Decision                             │
│  • Public: All users                         │
│  • Private: Whitelist check                  │
│  • Paid: Premium & active check              │
│  • Test: Premium or whitelisted              │
└──────────┬───────────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌────────────┐
│ ALLOW  │   │   DENY     │
└────────┘   └────────────┘
    │             │
    ▼             ▼
┌────────────────────────┐
│ Show Categories        │ or │ Request Access
└────────────────────────┘
```

### Content Delivery Flow
```
┌──────────────────────────────────┐
│  User Selects Category           │
│  callback_data: cat_1            │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  GET /api/categories/1/contents/ │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Check Each Content:             │
│  • is_active                     │
│  • is_premium (if applicable)    │
│  • user has category access      │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Display Contents List           │
│  with inline buttons             │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  User Selects Content            │
│  callback_data: content_5        │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  GET /api/content/5/             │
│  • Increment views               │
│  • Return full content           │
│  • Show rating buttons           │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  User Rates Content              │
│  POST /api/content/5/rate/       │
│  {rating: 5, user_id: "123"}     │
└──────────────────────────────────┘
```

---

## Admin Panel Structure

```
Django Admin Panel
│
├── Home Dashboard
│   └── Stats & recent actions
│
├── AUTHENTICATION & AUTHORIZATION
│   ├── Users
│   ├── Groups
│   └── Permissions
│
├── CORE APP
│   ├── Bot Settings
│   │   ├── ✏️ Edit token
│   │   ├── ✏️ Change access mode
│   │   ├── ✏️ Enable/Disable
│   │   └── 📜 Audit Log
│   │
│   └── Telegram Bot Handler (future)
│
├── CONTENT APP
│   ├── Categories
│   │   ├── ➕ Create category
│   │   ├── 📁 Parent/Child hierarchy
│   │   ├── 🎯 Set featured status
│   │   ├── 📸 Upload icon
│   │   └── ↕️ Reorder
│   │
│   ├── Contents
│   │   ├── ➕ Create content
│   │   ├── 📝 Edit body (markdown)
│   │   ├── 📸 Upload images
│   │   ├── 🎬 Add video URLs
│   │   ├── 💎 Mark premium
│   │   ├── 📊 View statistics
│   │   └── ⭐ View ratings
│   │
│   └── Content Ratings
│       ├── 👁️ View user feedback
│       ├── ⭐ See ratings
│       └── 💬 Read comments
│
└── ACCESS CONTROL APP
    ├── Bot Users
    │   ├── 👤 View all users
    │   ├── ✅ Whitelist users
    │   ├── 💎 Grant premium
    │   ├── 🚫 Block users
    │   └── 📊 View statistics
    │
    ├── User Category Access
    │   ├── ➕ Assign categories
    │   ├── 🔓 Grant access
    │   ├── 🔐 Revoke access
    │   └── ⏰ Set expiration
    │
    ├── Subscription Plans
    │   ├── ➕ Create plan
    │   ├── 💰 Set pricing
    │   ├── ⏱️ Set duration
    │   └── ✨ Add features
    │
    └── User Subscriptions
        ├── 👁️ View subscriptions
        ├── ✅ Active/Expired
        ├── 💳 Payment history
        └── ❌ Cancel subscriptions
```

---

## Database Schema

### Core App Tables
```
bot_settings
├── id (PK)
├── telegram_token
├── telegram_nickname
├── whatsapp_phone_number (nullable)
├── whatsapp_api_key (nullable)
├── access_mode (public|private|paid|test)
├── is_active
├── description
├── created_at
└── updated_at

audit_log
├── id (PK)
├── user_id (FK → auth_user)
├── action (create|update|delete|access)
├── model_name
├── object_id
├── changes (JSON)
├── timestamp
└── ip_address
```

### Content App Tables
```
category
├── id (PK)
├── name
├── slug (UNIQUE)
├── description
├── parent_id (FK → self, nullable)
├── icon (ImageField)
├── thumbnail (ImageField)
├── order
├── is_active
├── is_featured
├── created_at
└── updated_at

content
├── id (PK)
├── title
├── slug
├── description
├── body (TextField with markdown)
├── content_type (text|image|video|file|link|quiz)
├── category_id (FK → category)
├── tags
├── image (ImageField)
├── media_url
├── file (FileField)
├── author_id (FK → auth_user)
├── order
├── is_active
├── is_featured
├── is_premium
├── views_count
├── created_at
├── updated_at
└── published_at

content_rating
├── id (PK)
├── content_id (FK → content)
├── user_id (string - Telegram/WhatsApp ID)
├── rating (1-5)
├── comment
└── created_at
```

### Access Control App Tables
```
bot_user
├── id (PK)
├── user_id (unique - Telegram/WhatsApp)
├── platform (telegram|whatsapp|both)
├── username
├── phone
├── is_active
├── is_premium
├── is_whitelisted
├── premium_until (nullable)
├── first_interaction
├── last_interaction
├── interaction_count
└── notes

user_category_access
├── id (PK)
├── user_id (FK → bot_user)
├── category_id (FK → category)
├── is_allowed
├── granted_at
└── expires_at (nullable)

subscription_plan
├── id (PK)
├── name (unique)
├── slug (unique)
├── description
├── price
├── duration_days
├── features (JSON)
├── is_active
├── display_order
└── created_at

user_subscription
├── id (PK)
├── user_id (FK → bot_user)
├── plan_id (FK → subscription_plan)
├── status (active|expired|cancelled)
├── started_at
├── expires_at
├── cancelled_at (nullable)
└── transaction_id
```

---

## API Response Examples

### Check Access
```json
{
  "user_id": "123456789",
  "access_mode": "public",
  "has_access": true,
  "is_active": true,
  "is_premium": false,
  "is_whitelisted": false
}
```

### Category List
```json
[
  {
    "id": 1,
    "name": "Mathematics",
    "slug": "mathematics",
    "description": "Math lessons",
    "icon": "https://...",
    "children": [
      {
        "id": 2,
        "name": "Algebra",
        "slug": "algebra",
        "children": []
      }
    ],
    "content_count": 15
  }
]
```

### Content Detail
```json
{
  "id": 5,
  "title": "Quadratic Equations",
  "slug": "quadratic-equations",
  "description": "Learn about quadratic equations",
  "body": "A quadratic equation is...",
  "content_type": "text",
  "category": 2,
  "category_name": "Algebra",
  "image": "https://...",
  "is_premium": false,
  "views_count": 245,
  "average_rating": 4.7,
  "rating_count": 15,
  "author": 1,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Deployment Architecture

### Development
```
Local Machine
├── Django (runserver)
├── SQLite database
└── Static files (local)
```

### Production
```
┌─────────────────────────────────────────┐
│         Cloud Provider (AWS/Azure/GCP)  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │    Load Balancer / Reverse Proxy│    │
│  │    (Nginx / Apache)             │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│  ┌────────────▼────────────────────┐    │
│  │   Django Application (Gunicorn) │ x4 │
│  │   Instances                     │    │
│  └────────────┬────────────────────┘    │
│               │                         │
│  ┌────────────▼────────────────────┐    │
│  │   PostgreSQL Database           │    │
│  │   (with backups)                │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   S3 / Cloud Storage            │    │
│  │   (media & static files)        │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   Redis Cache                   │    │
│  │   (sessions & caching)          │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   Celery Workers (async tasks)  │    │
│  │   (email, notifications)        │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

---

## Integration Points

### Telegram Bot ↔ Django
```
Telegram User
    ↓ (Telegram API)
python-telegram-bot
    ↓ (HTTP)
Django REST API
    ↓ (Database queries)
PostgreSQL Database
```

### WhatsApp Bot ↔ Django (Future)
```
WhatsApp User
    ↓ (Twilio API)
Twilio Handler
    ↓ (HTTP Webhooks)
Django Views
    ↓ (Database queries)
PostgreSQL Database
```

### Website ↔ Django (Future)
```
Web Browser
    ↓ (HTTP/HTTPS)
Django Templates / React Frontend
    ↓ (REST API)
Django REST API
    ↓ (Database queries)
PostgreSQL Database
```

---

## Security Layers

```
┌─────────────────────────────────────┐
│  External Access (Bot/Website)      │
├─────────────────────────────────────┤
│ HTTPS / TLS Encryption              │
├─────────────────────────────────────┤
│ API Authentication                  │
│ (Token/OAuth for admin)             │
├─────────────────────────────────────┤
│ Input Validation & Sanitization     │
├─────────────────────────────────────┤
│ Django ORM (prevents SQL injection) │
├─────────────────────────────────────┤
│ Database Access Control (roles)     │
├─────────────────────────────────────┤
│ Encrypted Password Storage (PBKDF2) │
├─────────────────────────────────────┤
│ Audit Logging (AuditLog model)      │
└─────────────────────────────────────┘
```

---

## Scaling Considerations

### Current Setup (Development)
- Single Django instance
- SQLite database
- Local file storage
- Perfect for small/medium bots

### Future Scaling (Production)
1. **Database** - PostgreSQL with replication
2. **Caching** - Redis for sessions and query cache
3. **Storage** - S3/Cloud Storage for media
4. **App Servers** - Multiple Gunicorn instances
5. **Task Queue** - Celery for async operations
6. **Load Balancing** - Nginx/HAProxy
7. **Monitoring** - Prometheus/Grafana
8. **CDN** - CloudFlare for static assets

---

This architecture is designed to be:
- ✅ **Scalable** - Grows with your bot
- ✅ **Maintainable** - Clear separation of concerns
- ✅ **Secure** - Multiple security layers
- ✅ **Extensible** - Ready for Telegram/WhatsApp/Website
- ✅ **Production-ready** - Best practices throughout
