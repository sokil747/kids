"""Views for access control API."""
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import BotUser, SubscriptionPlan
from .serializers import BotUserSerializer, SubscriptionPlanSerializer


class CheckUserAccess(generics.GenericAPIView):
    """Check if user has access based on access mode."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id, access_mode):
        """Check user access."""
        try:
            user = BotUser.objects.get(user_id=user_id)
            has_access = user.has_access(access_mode)
            
            return Response({
                'user_id': user_id,
                'access_mode': access_mode,
                'has_access': has_access,
                'is_active': user.is_active,
                'is_premium': user.is_premium_active(),
                'is_whitelisted': user.is_whitelisted,
            })
        except BotUser.DoesNotExist:
            return Response({
                'user_id': user_id,
                'access_mode': access_mode,
                'has_access': access_mode == 'public',
                'message': 'New user'
            }, status=status.HTTP_404_NOT_FOUND)


class BotUserDetail(generics.RetrieveUpdateAPIView):
    """Get or update bot user."""
    serializer_class = BotUserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'user_id'
    
    def get_queryset(self):
        return BotUser.objects.all()
    
    def get_object(self):
        """Get or create user on first access."""
        user_id = self.kwargs['user_id']
        user, created = BotUser.objects.get_or_create(
            user_id=user_id,
            defaults={'platform': 'telegram'}
        )
        return user


class LogInteraction(generics.GenericAPIView):
    """Log user interaction with bot."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, user_id):
        """Log interaction and update user."""
        try:
            user = BotUser.objects.get(user_id=user_id)
            user.increment_interaction()
            serializer = BotUserSerializer(user)
            return Response(serializer.data)
        except BotUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SubscriptionPlansList(generics.ListAPIView):
    """Get all active subscription plans."""
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('display_order')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionPlanDetail(generics.RetrieveAPIView):
    """Get subscription plan details."""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]
