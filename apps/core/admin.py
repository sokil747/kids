"""Admin configuration for core app."""
from django.contrib import admin
from django.utils.html import format_html
from .models import BotSettings, AuditLog


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    """Admin interface for BotSettings with enhanced UI."""
    
    fieldsets = (
        ('Telegram Configuration', {
            'fields': ('telegram_token', 'telegram_nickname'),
            'description': 'Configure your Telegram bot credentials'
        }),
        ('WhatsApp Configuration (Future)', {
            'fields': ('whatsapp_phone_number', 'whatsapp_api_key'),
            'classes': ('collapse',),
            'description': 'Set up WhatsApp integration for future use'
        }),
        ('Access Control', {
            'fields': ('access_mode', 'is_active'),
            'description': 'Control who can access the bot'
        }),
        ('Welcome Messages', {
            'fields': ('authorized_welcome_message', 'unauthorized_welcome_message'),
            'classes': ('wide',),
            'description': 'Customize welcome messages for different user types'
        }),
        ('Additional Info', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Read-only timestamps'
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('telegram_nickname', 'access_mode_badge', 'is_active_badge', 'updated_at')
    list_filter = ('access_mode', 'is_active', 'created_at')
    search_fields = ('telegram_nickname', 'description')
    
    actions = ['activate_bot', 'deactivate_bot', 'switch_to_public', 'switch_to_private']
    
    def access_mode_badge(self, obj):
        """Display access mode as a colored badge."""
        colors = {
            'public': '#28a745',
            'private': '#dc3545',
            'paid': '#ffc107',
            'test': '#17a2b8',
        }
        color = colors.get(obj.access_mode, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_access_mode_display()
        )
    access_mode_badge.short_description = 'Access Mode'
    
    def is_active_badge(self, obj):
        """Display active status as a colored badge."""
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_active_badge.short_description = 'Status'
    
    def activate_bot(self, request, queryset):
        """Action to activate selected bots."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} bot(s) activated.')
    activate_bot.short_description = 'Activate selected bots'
    
    def deactivate_bot(self, request, queryset):
        """Action to deactivate selected bots."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} bot(s) deactivated.')
    deactivate_bot.short_description = 'Deactivate selected bots'
    
    def switch_to_public(self, request, queryset):
        """Switch bot to public mode."""
        updated = queryset.update(access_mode='public')
        self.message_user(request, f'{updated} bot(s) switched to public mode.')
    switch_to_public.short_description = 'Switch to Public mode'
    
    def switch_to_private(self, request, queryset):
        """Switch bot to private mode."""
        updated = queryset.update(access_mode='private')
        self.message_user(request, f'{updated} bot(s) switched to private mode.')
    switch_to_private.short_description = 'Switch to Private mode'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog - read-only."""
    
    list_display = ('user', 'action', 'model_name', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'timestamp', 'ip_address')
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False
