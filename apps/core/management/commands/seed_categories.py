from django.core.management.base import BaseCommand
from apps.content.models import Tag


class Command(BaseCommand):
    help = 'Seed initial tags: Ukraine and Poland'

    def handle(self, *args, **options):
        ukraine, created = Tag.objects.get_or_create(
            name='Ukraine',
            slug='ukraine',
            defaults={
                'flag_unicode': '🇺🇦',
                'order': 0,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created tag: {ukraine}'))
        else:
            ukraine.flag_unicode = '🇺🇦'
            ukraine.save(update_fields=['flag_unicode'])
            self.stdout.write(f'Updated tag: {ukraine}')

        poland, created = Tag.objects.get_or_create(
            name='Poland',
            slug='poland',
            defaults={
                'flag_unicode': '🇵🇱',
                'order': 1,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created tag: {poland}'))
        else:
            poland.flag_unicode = '🇵🇱'
            poland.save(update_fields=['flag_unicode'])
            self.stdout.write(f'Updated tag: {poland}')
