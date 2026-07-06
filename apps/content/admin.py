"""
Content admin configuration with advanced UI for hierarchy management.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Tag, Category, Content, ContentRating, Business
from .import_utils import extract_spreadsheet_id, fetch_sheet_csv, parse_rows, find_duplicates, DEFAULT_SHEET_URL


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for country tags."""
    list_display = ('flag_display', 'name', 'order', 'is_active', 'is_active_badge')
    list_display_links = ('name',)
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    list_editable = ('order', 'is_active')

    actions = ['enable_tags', 'disable_tags']

    def flag_display(self, obj):
        return obj.flag_unicode or '—'
    flag_display.short_description = 'Flag'

    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('gsheet-import/', self.admin_site.admin_view(self.gsheet_import_view), name='content_business_gsheet_import'),
        ] + urls

    def gsheet_import_view(self, request):
        if request.method == 'POST':
            action = request.POST.get('action')
            sheet_url = request.POST.get('sheet_url', '').strip()

            if action == 'preview':
                sheet_id = extract_spreadsheet_id(sheet_url)
                if not sheet_id:
                    messages.error(request, "Не вдалося знайти ID таблиці у вказаному посиланні")
                    return redirect('admin:content_business_gsheet_import')

                try:
                    csv_text = fetch_sheet_csv(sheet_id)
                    rows = parse_rows(csv_text)
                except Exception as e:
                    messages.error(request, f"Помилка отримання даних з таблиці: {e}")
                    return redirect('admin:content_business_gsheet_import')

                if not rows:
                    messages.warning(request, "Не знайдено жодного рядка з назвою мережі")
                    return redirect('admin:content_business_gsheet_import')

                duplicates = find_duplicates(rows)
                dup_count = 0
                for r in rows:
                    key = r['title'].lower()
                    r['_is_duplicate'] = key in duplicates
                    r['_existing_id'] = duplicates[key].id if key in duplicates else None
                    if r['_is_duplicate']:
                        dup_count += 1

                request.session['gsheet_import_rows'] = rows
                request.session['gsheet_import_url'] = sheet_url

                ctx = {
                    **self.admin_site.each_context(request),
                    'rows': rows,
                    'sheet_url': sheet_url,
                    'dup_count': dup_count,
                    'new_count': len(rows) - dup_count,
                    'title': 'Попередній перегляд імпорту',
                    'opts': self.model._meta,
                }
                return render(request, 'admin/content/business/gsheet_import.html', ctx)

            if action == 'confirm':
                rows = request.session.get('gsheet_import_rows', [])
                if not rows:
                    messages.error(request, "Сесія порожня. Будь ласка, виконайте попередній перегляд ще раз")
                    return redirect('admin:content_business_gsheet_import')

                import re as re_lib
                import urllib.request as url_req
                from django.core.files.base import ContentFile

                skip_ids = set(request.POST.getlist('skip'))
                updated = 0
                created = 0
                skipped = 0

                for r in rows:
                    rkey = str(r.get('_existing_id') or '')
                    if rkey in skip_ids:
                        skipped += 1
                        continue

                    defaults = {k: v for k, v in r.items() if not k.startswith('_')}

                    if r.get('_is_duplicate'):
                        Business.objects.filter(id=r['_existing_id']).update(**defaults)
                        biz = Business.objects.get(id=r['_existing_id'])
                        updated += 1
                    else:
                        biz = Business.objects.create(**defaults)
                        created += 1

                    photo_url = r.get('_photo_url')
                    if photo_url and biz:
                        m = re_lib.search(r'/d/([a-zA-Z0-9_-]+)', photo_url)
                        if m:
                            file_id = m.group(1)
                            dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                            try:
                                img_resp = url_req.urlopen(dl_url, timeout=15)
                                biz.logo.save(f"{file_id}.jpg", ContentFile(img_resp.read()), save=True)
                            except Exception:
                                pass

                request.session.pop('gsheet_import_rows', None)
                request.session.pop('gsheet_import_url', None)
                messages.success(request, f"Імпорт завершено. Створено: {created}, оновлено: {updated}, пропущено: {skipped}")
                return redirect('admin:content_business_changelist')

        sheet_url = request.session.get('gsheet_import_url', DEFAULT_SHEET_URL)
        ctx = {
            **self.admin_site.each_context(request),
            'sheet_url': sheet_url,
            'title': 'Імпорт бізнесів з Google Таблиці',
            'opts': self.model._meta,
        }
        return render(request, 'admin/content/business/gsheet_import.html', ctx)


@admin.register(ContentRating)
class ContentRatingAdmin(admin.ModelAdmin):
    """Admin for content ratings."""
    
    list_display = ('content', 'rating_display', 'user_id', 'created_at')
    list_filter = ('rating', 'created_at', 'content__category')
    search_fields = ('content__title', 'user_id', 'comment')
    readonly_fields = ('content', 'user_id', 'rating', 'comment', 'created_at')
    
    def has_add_permission(self, request):
        """Ratings are created by bot users, not admins."""
        return False
    
    def rating_display(self, obj):
        """Display rating as stars."""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: gold; font-size: 16px;">{}</span>',
            stars
        )
    rating_display.short_description = 'Rating'


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'logo', 'description', 'emoji')
        }),
        ('Contact & Location', {
            'fields': ('address', 'geo_coordinates', 'hotline', 'hotline_label'),
        }),
        ('Social Media & Links', {
            'fields': ('online_store', 'facebook', 'instagram', 'tiktok', 'youtube'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('tags', 'categories', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    list_display = ('title', 'business_tags', 'business_categories', 'is_active_badge', 'updated_at')
    list_filter = ('is_active', 'tags', 'categories')
    search_fields = ('title', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags', 'categories')
    change_list_template = 'admin/content/business/change_list.html'

    def business_tags(self, obj):
        return ", ".join(str(t) for t in obj.tags.all()) or "—"
    business_tags.short_description = 'Tags'

    def business_categories(self, obj):
        return ", ".join(str(c) for c in obj.categories.all()[:3]) or "—"
    business_categories.short_description = 'Categories'

    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'
