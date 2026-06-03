"""
Core models for bot settings and configuration.
"""
from django.db import models
from django.core.exceptions import ValidationError


class BotSettings(models.Model):
    """
    Centralized settings for Telegram and WhatsApp bots.
    Allows dynamic configuration without code changes.
    """
    
    # Bot identification
    telegram_token = models.CharField(
        max_length=500,
        help_text="Telegram bot token from BotFather"
    )
    telegram_nickname = models.CharField(
        max_length=100,
        unique=True,
        default='ContentMentor',
        help_text="Bot username/nickname (without @)"
    )
    
    # WhatsApp configuration (for future use)
    whatsapp_phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="WhatsApp Business Account phone number"
    )
    whatsapp_api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="WhatsApp API key from Twilio or provider"
    )
    
    # Access control settings
    ACCESS_MODES = (
        ('public', 'Public - Anyone can access'),
        ('private', 'Private - Only whitelisted users'),
        ('paid', 'Paid - Subscription/payment required'),
        ('test', 'Test - Limited access for testing'),
    )
    
    access_mode = models.CharField(
        max_length=20,
        choices=ACCESS_MODES,
        default='public',
        help_text="Access control mode for the bot"
    )
    
    # Status and metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable the bot"
    )
    description = models.TextField(
        blank=True,
        help_text="Bot description and purpose"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Bot Settings"
        ordering = ['-created_at']
        db_table = 'core_bot_settings'
    
    def __str__(self):
        return f"{self.telegram_nickname} ({self.get_access_mode_display()})"
    
    def clean(self):
        """Validate settings."""
        if not self.telegram_token:
            raise ValidationError("Telegram token is required")
        if not self.telegram_nickname:
            raise ValidationError("Telegram nickname is required")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        # Ensure only one active settings object in private/test modes
        if self.is_active and self.access_mode in ['private', 'test']:
            BotSettings.objects.filter(
                is_active=True,
                access_mode=self.access_mode
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """
    Audit trail for admin actions on bot configuration.
    """
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('access', 'Access'),
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"
