"""Serializers for access control API."""
from rest_framework import serializers
from .models import BotUser, SubscriptionPlan, UserSubscription


class BotUserSerializer(serializers.ModelSerializer):
    """Serializer for BotUser model."""
    
    is_premium_active = serializers.SerializerMethodField()
    
    class Meta:
        model = BotUser
        fields = [
            'id', 'user_id', 'platform', 'username', 'phone',
            'is_active', 'is_whitelisted', 'is_premium', 'premium_until',
            'is_premium_active', 'interaction_count', 'first_interaction',
            'last_interaction'
        ]
        read_only_fields = ['first_interaction', 'last_interaction', 'interaction_count']
    
    def get_is_premium_active(self, obj):
        """Check if premium is currently active."""
        return obj.is_premium_active()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model."""
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'slug', 'description', 'price', 'duration_days', 'features']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model."""
    
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'plan', 'status', 'started_at', 'expires_at', 'is_active']
    
    def get_is_active(self, obj):
        """Check if subscription is active."""
        return obj.is_active_subscription()
