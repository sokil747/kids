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
            'expand_children_inline': True,
        }
    )
    if created:
        self.stdout.write(self.style.SUCCESS(f'Created: {ukraine}'))
    else:
        ukraine.expand_children_inline = True
        ukraine.save(update_fields=['expand_children_inline'])
        self.stdout.write(f'Updated: {ukraine}')

    poland, created = Category.objects.get_or_create(
        name='Poland',
        slug='poland',
        defaults={
            'description': 'Content about Poland',
            'order': 1,
            'is_active': True,
            'is_featured': True,
            'expand_children_inline': True,
        }
    )
    if created:
        self.stdout.write(self.style.SUCCESS(f'Created: {poland}'))
    else:
        poland.expand_children_inline = True
        poland.save(update_fields=['expand_children_inline'])
        self.stdout.write(f'Updated: {poland}')
