"""
Content admin configuration with advanced UI for hierarchy management.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Tag, Category, Content, ContentRating, Business


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

    def enable_tags(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} tag(s) enabled.')
    enable_tags.short_description = 'Enable selected tags'

    def disable_tags(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} tag(s) disabled.')
    disable_tags.short_description = 'Disable selected tags'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for hierarchical category management."""
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'cta_message')
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': 'Select a parent category to create subcategories'
        }),
        ('Media', {
            'fields': ('icon', 'thumbnail'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active', 'is_featured', 'show_flag', 'inline_display', 'expand_children_inline'),
            'description': 'Expand in place shows children in the same message below parent buttons'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    list_display = ('hierarchy_display', 'is_active_badge', 'is_featured_badge', 'content_count', 'updated_at')
    list_filter = ('is_active', 'is_featured', 'parent', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    def hierarchy_display(self, obj):
        """Display category with hierarchy indentation."""
        depth = 0
        parent = obj.parent
        while parent:
            depth += 1
            parent = parent.parent
        
        indent = "─" * (depth * 2)
        return f"{indent} {obj.name}"
    hierarchy_display.short_description = 'Category'
    
    def is_active_badge(self, obj):
        """Display active status."""
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'
    
    def is_featured_badge(self, obj):
        """Display featured status."""
        if obj.is_featured:
            return format_html(
                '<span style="color: gold; font-size: 16px;">★</span>'
            )
        return '—'
    is_featured_badge.short_description = 'Featured'
    
    def content_count(self, obj):
        """Display number of direct contents."""
        count = obj.contents.count()
        return format_html(
            '<span style="background-color: #e7f3ff; padding: 2px 6px; border-radius: 3px;">{} items</span>',
            count
        )
    content_count.short_description = 'Contents'
    
    actions = ['activate_categories', 'deactivate_categories', 'mark_as_featured', 'remove_featured']
    
    def activate_categories(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} categories activated.')
    activate_categories.short_description = 'Activate selected categories'
    
    def deactivate_categories(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} categories deactivated.')
    deactivate_categories.short_description = 'Deactivate selected categories'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} categories marked as featured.')
    mark_as_featured.short_description = 'Mark as featured'
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'{queryset.count()} categories removed from featured.')
    remove_featured.short_description = 'Remove from featured'


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """Admin for content management with rich editing."""
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Categories / Tags', {
            'fields': ('categories',),
            'description': 'Assign additional categories to this content',
            'classes': ('wide',)
        }),
        ('Content', {
            'fields': ('content_type', 'body'),
            'classes': ('wide',)
        }),
        ('Media & Attachments', {
            'fields': ('image', 'media_url', 'file'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('tags', 'order')
        }),
        ('Access & Visibility', {
            'fields': ('is_active', 'is_featured', 'is_premium', 'published_at')
        }),
        ('Statistics', {
            'fields': ('views_count', 'author'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    list_display = ('title_with_category', 'content_type_badge', 'is_active_badge', 'is_premium_badge', 'views_count', 'updated_at')
    list_filter = ('content_type', 'is_active', 'is_premium', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'slug', 'description', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    filter_horizontal = ('categories',)
    
    def get_readonly_fields(self, request, obj=None):
        """Set author as read-only if content exists."""
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append('author')
        return readonly
    
    def save_model(self, request, obj, form, change):
        """Set author automatically."""
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def title_with_category(self, obj):
        """Display title with category."""
        return f"{obj.category.name} > {obj.title}"
    title_with_category.short_description = 'Content'
    
    def content_type_badge(self, obj):
        """Display content type with color."""
        colors = {
            'text': '#6c757d',
            'image': '#e83e8c',
            'video': '#fd7e14',
            'file': '#0dcaf0',
            'link': '#0d6efd',
            'quiz': '#6f42c1',
        }
        color = colors.get(obj.content_type, '#042630')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_content_type_display()
        )
    content_type_badge.short_description = 'Type'
    
    def is_active_badge(self, obj):
        """Display active status."""
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Published' if obj.is_active else 'Draft'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'
    
    def is_premium_badge(self, obj):
        """Display premium status."""
        if obj.is_premium:
            return format_html(
                '<span style="color: gold; font-weight: bold;">💎 Premium</span>'
            )
        return 'Free'
    is_premium_badge.short_description = 'Access'
    
    actions = ['publish_content', 'unpublish_content', 'mark_premium', 'mark_free']
    
    def publish_content(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} contents published.')
    publish_content.short_description = 'Publish selected contents'
    
    def unpublish_content(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} contents unpublished.')
    unpublish_content.short_description = 'Unpublish selected contents'
    
    def mark_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f'{queryset.count()} contents marked as premium.')
    mark_premium.short_description = 'Mark as premium'
    
    def mark_free(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f'{queryset.count()} contents marked as free.')
    mark_free.short_description = 'Mark as free'


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
            'fields': ('address', 'geo_coordinates', 'hotline'),
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
