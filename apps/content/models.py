"""
Content models for hierarchical category and content management.
Designed to work with both Telegram and WhatsApp bots.
"""
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Tag(models.Model):
    """
    Country tags shown at the top level of the bot menu.
    After selecting a tag, associated categories are shown.
    """
    name = models.CharField(max_length=200, help_text="Tag name (e.g. Ukraine)")
    slug = models.SlugField(unique=True, help_text="URL-friendly identifier")
    flag_unicode = models.CharField(
        max_length=10, blank=True,
        help_text="Unicode flag character (e.g. 🇺🇦, 🇵🇱)"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        db_table = 'content_tag'

    def __str__(self):
        return f"{self.flag_unicode or ''} {self.name}".strip()


class Category(models.Model):
    """
    Hierarchical category structure for organizing content.
    Supports unlimited nesting levels.
    """
    
    # Basic info
    name = models.CharField(
        max_length=200,
        help_text="Category name"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    cta_message = models.CharField(
        max_length=500,
        blank=True,
        help_text="Call-to-action message shown when this category's subcategories are displayed (e.g. 'Choose country:')"
    )
    
    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category for hierarchy"
    )
    # Media
    icon = models.ImageField(
        upload_to='category_icons/',
        null=True,
        blank=True,
        help_text="Category icon for bot display"
    )
    thumbnail = models.ImageField(
        upload_to='category_thumbnails/',
        null=True,
        blank=True,
        help_text="Thumbnail for preview"
    )
    
    # Metadata
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within parent category"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Show/hide category in bot"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this category in main menu"
    )
    inline_display = models.BooleanField(
        default=False,
        help_text="Show subcategories as inline buttons (single row) instead of stacked"
    )
    expand_children_inline = models.BooleanField(
        default=True,
        help_text="Show children in the same message below parent buttons (True) or send as a new message (False)"
    )
    show_flag = models.BooleanField(
        default=True,
        help_text="Show flag emoji / tag flag at the start of the category name in the bot"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['parent_id', 'order', 'name']
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
        db_table = 'content_category'
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_breadcrumb(self):
        """Get full category path."""
        breadcrumb = [self.name]
        parent = self.parent
        while parent:
            breadcrumb.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(breadcrumb)
    
    def get_all_children(self, include_self=False):
        """Get all descendants recursively."""
        children = list(self.children.all())
        if include_self:
            return [self] + children
        
        all_children = children.copy()
        for child in children:
            all_children.extend(child.get_all_children())
        return all_children


class Content(models.Model):
    """
    Content items organized within categories.
    Supports rich content types.
    """
    
    CONTENT_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('link', 'Link'),
        ('quiz', 'Quiz'),
    )
    
    # Identification
    title = models.CharField(
        max_length=300,
        help_text="Content title"
    )
    slug = models.SlugField(
        help_text="URL-friendly identifier"
    )
    
    # Content type and body
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        default='text',
        help_text="Type of content"
    )
    description = models.TextField(
        help_text="Short description for preview"
    )
    body = models.TextField(
        help_text="Main content (supports markdown)"
    )
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='contents',
        help_text="Primary category"
    )
    categories = models.ManyToManyField(
        Category,
        related_name='tagged_contents',
        blank=True,
        help_text="Additional categories/tags for this content"
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for search"
    )
    
    # Media attachments
    image = models.ImageField(
        upload_to='content_images/',
        null=True,
        blank=True,
        help_text="Featured image"
    )
    media_url = models.URLField(
        blank=True,
        help_text="External media URL (video, audio, etc.)"
    )
    file = models.FileField(
        upload_to='content_files/',
        null=True,
        blank=True,
        help_text="Downloadable file"
    )
    
    # Metadata
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_content'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within category"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Publish/unpublish content"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature in category"
    )
    views_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of views"
    )
    
    # Access control
    is_premium = models.BooleanField(
        default=False,
        help_text="Only for paid users"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Publication date"
    )
    
    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug', 'category']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = ('category', 'slug')
        db_table = 'content_content'
    
    def __str__(self):
        return f"{self.category.name} > {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def increment_views(self):
        """Increment view counter."""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class ContentRating(models.Model):
    """
    User ratings and feedback for content.
    """
    
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user_id = models.CharField(
        max_length=100,
        help_text="Telegram/WhatsApp user ID"
    )
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        blank=True,
        help_text="User feedback"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('content', 'user_id')
        ordering = ['-created_at']
        db_table = 'content_rating'
    
    def __str__(self):
        return f"{self.content.title} - {self.rating}★"


class Business(models.Model):
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True, help_text="Business logo")
    title = models.CharField(max_length=300, help_text="Business name")
    address = models.TextField(blank=True, help_text="Physical address")
    geo_coordinates = models.CharField(max_length=100, blank=True, help_text="Coordinates (lat,lng) — auto-detected from address but can be edited")
    description = models.TextField(blank=True, help_text="Business description")
    online_store = models.URLField(blank=True, help_text="Online store URL")
    facebook = models.URLField(blank=True, help_text="Facebook page URL")
    instagram = models.URLField(blank=True, help_text="Instagram URL")
    tiktok = models.URLField(blank=True, help_text="TikTok URL")
    youtube = models.URLField(blank=True, help_text="YouTube URL")
    hotline = models.CharField(max_length=100, blank=True, help_text="Hotline phone number")
    
    emoji = models.CharField(max_length=10, blank=True, default="🎁", help_text="Emoji shown before the business name in bot lists (leave blank to hide)")

    tags = models.ManyToManyField(Tag, related_name='businesses', blank=True, help_text="Country tags")
    categories = models.ManyToManyField(Category, related_name='businesses', blank=True, help_text="Associated categories")

    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True, help_text="Publish/unpublish")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        db_table = 'content_business'

    def __str__(self):
        return self.title
