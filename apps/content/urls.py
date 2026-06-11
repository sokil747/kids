"""URL configuration for content API."""
from django.urls import path
from . import views

urlpatterns = [
    # Tags
    path('tags/', views.TagsList.as_view(), name='tags_list'),
    
    # Categories
    path('categories/', views.CategoriesList.as_view(), name='categories_list'),
    path('categories/<int:pk>/', views.CategoryDetail.as_view(), name='category_detail'),
    path('categories/<int:pk>/contents/', views.CategoryContents.as_view(), name='category_contents'),
    
    # Content
    path('content/', views.ContentList.as_view(), name='content_list'),
    path('content/<int:pk>/', views.ContentDetail.as_view(), name='content_detail'),
    path('content/<int:pk>/rate/', views.RateContent.as_view(), name='rate_content'),
    
    # Businesses
    path('businesses/', views.BusinessList.as_view(), name='business_list'),
    path('businesses/<int:pk>/', views.BusinessDetail.as_view(), name='business_detail'),
    path('categories/<int:pk>/businesses/', views.BusinessByCategory.as_view(), name='category_businesses'),
]
