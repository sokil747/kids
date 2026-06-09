from django.core.management.base import BaseCommand
from apps.content.models import Category


class Command(BaseCommand):
    help = 'Seed initial categories: Ukraine and Poland'

    def handle(self, *args, **options):
        ukraine, created = Category.objects.get_or_create(
            name='Ukraine',
            slug='ukraine',
            defaults={
                'description': 'Content about Ukraine',
                'order': 0,
                'is_active': True,
                'is_featured': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {ukraine}'))
        else:
            self.stdout.write(f'Already exists: {ukraine}')

        poland, created = Category.objects.get_or_create(
            name='Poland',
            slug='poland',
            defaults={
                'description': 'Content about Poland',
                'order': 1,
                'is_active': True,
                'is_featured': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {poland}'))
        else:
            self.stdout.write(f'Already exists: {poland}')
