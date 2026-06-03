"""Access control admin interface."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import BotUser, UserCategoryAccess, SubscriptionPlan, UserSubscription


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    """Admin for managing bot users and their access."""
    
    fieldsets = (
        ('User Information', {
            'fields': ('user_id', 'platform', 'username', 'phone')
        }),
        ('Access Control', {
            'fields': ('is_active', 'is_whitelisted', 'is_premium', 'premium_until'),
            'description': 'Manage user access permissions'
        }),
        ('Subscription', {
            'fields': ('is_premium_active_display',),
            'classes': ('collapse',)
        }),
        ('Activity', {
            'fields': ('first_interaction', 'last_interaction', 'interaction_count'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('wide',)
        }),
    )
    
    list_display = (
        'user_display', 'platform_badge', 'active_badge',
        'whitelist_badge', 'premium_badge', 'last_interaction'
    )
    list_filter = (
        'platform', 'is_active', 'is_whitelisted', 'is_premium',
        'first_interaction', 'last_interaction'
    )
    search_fields = ('user_id', 'username', 'phone')
    readonly_fields = ('first_interaction', 'last_interaction', 'interaction_count', 'is_premium_active_display')
    
    actions = [
        'activate_users', 'deactivate_users',
        'whitelist_users', 'remove_from_whitelist',
        'grant_premium_30days', 'grant_premium_90days',
        'revoke_premium'
    ]
    
    filter_horizontal = ()
    
    def user_display(self, obj):
        """Display user with username if available."""
        if obj.username:
            return f"@{obj.username} ({obj.user_id})"
        return obj.user_id
    user_display.short_description = 'User'
    
    def platform_badge(self, obj):
        """Display platform as colored badge."""
        colors = {'telegram': '#0088cc', 'whatsapp': '#22c55e', 'both': '#8b5cf6'}
        color = colors.get(obj.platform, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_platform_display()
        )
    platform_badge.short_description = 'Platform'
    
    def active_badge(self, obj):
        """Display active status."""
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Blocked'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    active_badge.short_description = 'Status'
    
    def whitelist_badge(self, obj):
        """Display whitelist status."""
        if obj.is_whitelisted:
            return format_html('<span style="color: #0dcaf0; font-weight: bold;">✓ Whitelisted</span>')
        return '—'
    whitelist_badge.short_description = 'Whitelisted'
    
    def premium_badge(self, obj):
        """Display premium status with expiry."""
        if obj.is_premium:
            if obj.premium_until:
                expires = obj.premium_until.strftime('%Y-%m-%d')
                color = '#28a745' if obj.is_premium_active() else '#ffc107'
                return format_html(
                    '<span style="color: {}; font-weight: bold;">💎 expires {}</span>',
                    color, expires
                )
            return format_html('<span style="color: gold; font-weight: bold;">💎 Premium</span>')
        return '—'
    premium_badge.short_description = 'Premium'
    
    def is_premium_active_display(self, obj):
        """Display premium status in detail."""
        return obj.is_premium_active()
    is_premium_active_display.boolean = True
    is_premium_active_display.short_description = 'Premium Active'
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def whitelist_users(self, request, queryset):
        queryset.update(is_whitelisted=True)
        self.message_user(request, f'{queryset.count()} users whitelisted.')
    whitelist_users.short_description = 'Whitelist selected users'
    
    def remove_from_whitelist(self, request, queryset):
        queryset.update(is_whitelisted=False)
        self.message_user(request, f'{queryset.count()} users removed from whitelist.')
    remove_from_whitelist.short_description = 'Remove from whitelist'
    
    def grant_premium_30days(self, request, queryset):
        for user in queryset:
            user.grant_premium(days=30)
        self.message_user(request, f'Premium granted to {queryset.count()} users for 30 days.')
    grant_premium_30days.short_description = 'Grant premium for 30 days'
    
    def grant_premium_90days(self, request, queryset):
        for user in queryset:
            user.grant_premium(days=90)
        self.message_user(request, f'Premium granted to {queryset.count()} users for 90 days.')
    grant_premium_90days.short_description = 'Grant premium for 90 days'
    
    def revoke_premium(self, request, queryset):
        queryset.update(is_premium=False, premium_until=None)
        self.message_user(request, f'Premium revoked for {queryset.count()} users.')
    revoke_premium.short_description = 'Revoke premium access'


@admin.register(UserCategoryAccess)
class UserCategoryAccessAdmin(admin.ModelAdmin):
    """Admin for managing user access to specific categories."""
    
    list_display = ('user', 'category', 'access_badge', 'granted_at', 'expires_at')
    list_filter = ('is_allowed', 'granted_at', 'expires_at')
    search_fields = ('user__user_id', 'user__username', 'category__name')
    readonly_fields = ('granted_at',)
    
    actions = ['grant_access', 'deny_access']
    
    def access_badge(self, obj):
        """Display access status."""
        color = '#28a745' if obj.is_allowed and obj.is_access_valid() else '#dc3545'
        status = 'Allowed' if obj.is_allowed and obj.is_access_valid() else 'Denied'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    access_badge.short_description = 'Access'
    
    def grant_access(self, request, queryset):
        queryset.update(is_allowed=True)
        self.message_user(request, f'Access granted for {queryset.count()} entries.')
    grant_access.short_description = 'Grant access'
    
    def deny_access(self, request, queryset):
        queryset.update(is_allowed=False)
        self.message_user(request, f'Access denied for {queryset.count()} entries.')
    deny_access.short_description = 'Deny access'


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin for managing subscription plans."""
    
    list_display = ('name', 'price_display', 'duration_days', 'is_active_badge')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration_days')
        }),
        ('Features', {
            'fields': ('features',),
        }),
        ('Display', {
            'fields': ('is_active', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        """Display price formatted."""
        return f"${obj.price}"
    price_display.short_description = 'Price'
    
    def is_active_badge(self, obj):
        """Display active status."""
        color = '#28a745' if obj.is_active else '#dc3545'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """Admin for viewing user subscriptions."""
    
    list_display = ('user', 'plan', 'status_badge', 'expires_at', 'started_at')
    list_filter = ('status', 'plan', 'started_at', 'expires_at')
    search_fields = ('user__user_id', 'user__username', 'plan__name')
    readonly_fields = ('started_at', 'cancelled_at')
    
    fieldsets = (
        ('Subscription Info', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('started_at', 'expires_at', 'cancelled_at')
        }),
        ('Payment', {
            'fields': ('transaction_id',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['cancel_subscriptions']
    
    def status_badge(self, obj):
        """Display status with color."""
        colors = {'active': '#28a745', 'expired': '#ffc107', 'cancelled': '#dc3545'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def cancel_subscriptions(self, request, queryset):
        for sub in queryset:
            sub.cancel()
        self.message_user(request, f'{queryset.count()} subscriptions cancelled.')
    cancel_subscriptions.short_description = 'Cancel selected subscriptions'
    
    def has_add_permission(self, request):
        """Subscriptions are created programmatically."""
        return False
