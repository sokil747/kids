#!/bin/bash
# Quick setup script for ContentMentor Django project

set -e  # Exit on error

echo "🚀 ContentMentor Django Setup"
echo "=============================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

echo "✓ Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your settings"
else
    echo "✓ .env file exists"
fi

# Run migrations
echo "🗄️  Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo ""
echo "👤 Create superuser for admin access"
python manage.py createsuperuser

# Create initial bot settings
echo ""
echo "🤖 Creating initial bot settings..."
python manage.py shell << END
from apps.core.models import BotSettings

# Check if settings already exist
if not BotSettings.objects.exists():
    BotSettings.objects.create(
        telegram_token='8984157073:AAH3fcmGitmQhMDdZiaKVZ08swFvSgHfyuQ',
        telegram_nickname='kidsgenius_bot',
        access_mode='public',
        is_active=True,
        description='KidsGenius - Educational content for children'
    )
    print("✓ Bot settings created")
else:
    print("✓ Bot settings already exist")
END

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "2. Access the admin panel:"
echo "   http://localhost:8000/admin"
echo ""
echo "3. Create categories and content:"
echo "   Admin > Categories > Add Category"
echo "   Admin > Contents > Add Content"
echo ""
