"""URLs for access control API."""
from django.urls import path
from . import views

urlpatterns = [
    # User access checking
    path('check-access/<str:user_id>/<str:access_mode>/', views.CheckUserAccess.as_view(), name='check_access'),
    path('user/<str:user_id>/', views.BotUserDetail.as_view(), name='bot_user_detail'),
    path('user/<str:user_id>/interact/', views.LogInteraction.as_view(), name='log_interaction'),
    
    # Subscription plans
    path('plans/', views.SubscriptionPlansList.as_view(), name='subscription_plans'),
    path('plans/<int:pk>/', views.SubscriptionPlanDetail.as_view(), name='subscription_plan_detail'),
]
