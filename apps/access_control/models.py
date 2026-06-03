"""
User access control models for Telegram and WhatsApp bots.
Manages private/public/paid access modes by user ID.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class BotUser(models.Model):
    """
    Bot user profile for access control and tracking.
    Works with both Telegram and WhatsApp user IDs.
    """
    
    PLATFORM_CHOICES = (
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Both Platforms'),
    )
    
    # User identification
    user_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Telegram or WhatsApp user ID"
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='telegram',
        help_text="Which platform the user is from"
    )
    
    # User info
    username = models.CharField(
        max_length=255,
        blank=True,
        help_text="User's display name/username"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="User's phone number"
    )
    
    # Access control
    is_active = models.BooleanField(
        default=True,
        help_text="Allow/block user access"
    )
    is_premium = models.BooleanField(
        default=False,
        help_text="Premium/paid access granted"
    )
    
    # Whitelist for private mode
    is_whitelisted = models.BooleanField(
        default=False,
        help_text="Allowed in private mode"
    )
    
    # Metadata
    first_interaction = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)
    interaction_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of interactions with bot"
    )
    
    # Premium subscription
    premium_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Premium access expiration date"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Admin notes about user"
    )
    
    class Meta:
        ordering = ['-last_interaction']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['platform']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_premium']),
            models.Index(fields=['-last_interaction']),
        ]
        db_table = 'access_control_bot_user'
    
    def __str__(self):
        username_display = f"@{self.username}" if self.username else self.user_id
        return f"{username_display} ({self.get_platform_display()})"
    
    def has_access(self, access_mode):
        """
        Check if user has access based on bot access mode.
        
        access_mode: 'public', 'private', 'paid', or 'test'
        """
        if not self.is_active:
            return False
        
        if access_mode == 'public':
            return True
        elif access_mode == 'private':
            return self.is_whitelisted
        elif access_mode == 'paid':
            return self.is_premium and (
                not self.premium_until or 
                self.premium_until > timezone.now()
            )
        elif access_mode == 'test':
            return self.is_whitelisted or self.is_premium
        
        return False
    
    def is_premium_active(self):
        """Check if premium is still active."""
        return self.is_premium and (
            not self.premium_until or 
            self.premium_until > timezone.now()
        )
    
    def grant_premium(self, days=30):
        """Grant premium access for specified days."""
        self.is_premium = True
        self.premium_until = timezone.now() + timezone.timedelta(days=days)
        self.save()
    
    def increment_interaction(self):
        """Log a user interaction."""
        self.interaction_count += 1
        self.last_interaction = timezone.now()
        self.save(update_fields=['interaction_count', 'last_interaction'])


class UserCategoryAccess(models.Model):
    """
    Fine-grained category-level access control.
    Restrict access to specific categories per user.
    """
    
    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name='category_access'
    )
    category = models.ForeignKey(
        'content.Category',
        on_delete=models.CASCADE,
        related_name='user_access'
    )
    
    is_allowed = models.BooleanField(
        default=True,
        help_text="Allow/deny access to this category"
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Temporary access expiration"
    )
    
    class Meta:
        unique_together = ('user', 'category')
        db_table = 'access_control_user_category_access'
    
    def __str__(self):
        return f"{self.user} - {self.category}"
    
    def is_access_valid(self):
        """Check if access is currently valid."""
        if not self.is_allowed:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class SubscriptionPlan(models.Model):
    """
    Subscription plans for premium access.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Plan name (e.g., 'Basic', 'Pro', 'Premium')"
    )
    slug = models.SlugField(unique=True)
    description = models.TextField()
    
    # Pricing and duration
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in USD"
    )
    duration_days = models.PositiveIntegerField(
        help_text="Duration in days"
    )
    
    # Features
    features = models.JSONField(
        default=list,
        help_text="List of included features"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order']
        db_table = 'access_control_subscription_plan'
    
    def __str__(self):
        return f"{self.name} - ${self.price} for {self.duration_days} days"


class UserSubscription(models.Model):
    """
    Track user subscription history and current subscription.
    """
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(
        BotUser,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Dates
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Payment provider transaction ID"
    )
    
    class Meta:
        ordering = ['-started_at']
        db_table = 'access_control_user_subscription'
    
    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"
    
    def is_active_subscription(self):
        """Check if subscription is currently active."""
        return (
            self.status == 'active' and 
            self.expires_at > timezone.now()
        )
    
    def cancel(self):
        """Cancel subscription."""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()
