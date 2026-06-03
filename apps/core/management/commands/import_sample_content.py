"""
Django management command template for importing sample content.
Run with: python manage.py import_sample_content
"""
from django.core.management.base import BaseCommand
from apps.content.models import Category, Content
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Import sample categories and content for testing'

    def handle(self, *args, **options):
        self.stdout.write('Importing sample content...')
        
        # Get or create default admin user
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
        
        # Create sample categories
        categories_data = [
            {
                'name': 'Mathematics',
                'slug': 'mathematics',
                'description': 'Mathematics lessons and puzzles',
                'order': 1,
            },
            {
                'name': 'Science',
                'slug': 'science',
                'description': 'Science experiments and lessons',
                'order': 2,
            },
            {
                'name': 'Language',
                'slug': 'language',
                'description': 'Language learning and reading',
                'order': 3,
            },
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat.slug] = cat
            status = 'Created' if created else 'Exists'
            self.stdout.write(f"  {status}: {cat.name}")
        
        # Create subcategories
        subcategories_data = [
            {
                'name': 'Algebra',
                'slug': 'algebra',
                'parent_slug': 'mathematics',
                'order': 1,
            },
            {
                'name': 'Geometry',
                'slug': 'geometry',
                'parent_slug': 'mathematics',
                'order': 2,
            },
        ]
        
        for subcat_data in subcategories_data:
            parent_slug = subcat_data.pop('parent_slug')
            parent = categories[parent_slug]
            subcat, created = Category.objects.get_or_create(
                slug=subcat_data['slug'],
                defaults={**subcat_data, 'parent': parent}
            )
            categories[subcat.slug] = subcat
            status = 'Created' if created else 'Exists'
            self.stdout.write(f"  {status}: {subcat.name}")
        
        # Create sample content
        content_data = [
            {
                'title': 'Introduction to Algebra',
                'slug': 'intro-to-algebra',
                'description': 'Learn the basics of algebra',
                'body': 'Algebra is a branch of mathematics...',
                'category_slug': 'algebra',
                'content_type': 'text',
            },
            {
                'title': 'Geometry Basics',
                'slug': 'geometry-basics',
                'description': 'Understanding shapes and planes',
                'body': 'Geometry deals with shapes, sizes, and positions...',
                'category_slug': 'geometry',
                'content_type': 'text',
            },
        ]
        
        for content in content_data:
            category_slug = content.pop('category_slug')
            category = categories[category_slug]
            cont, created = Content.objects.get_or_create(
                slug=content['slug'],
                defaults={**content, 'category': category, 'author': admin}
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f"  {status}: {cont.title}")
        
        self.stdout.write(self.style.SUCCESS('✅ Sample content imported successfully!'))
