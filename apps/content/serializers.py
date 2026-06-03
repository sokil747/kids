"""Serializers for content API."""
from rest_framework import serializers
from .models import Category, Content, ContentRating


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    children = serializers.SerializerMethodField()
    content_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'icon', 'thumbnail', 'order', 'is_active', 'is_featured',
            'children', 'content_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children(self, obj):
        """Get subcategories recursively."""
        children = obj.children.filter(is_active=True).order_by('order')
        return CategorySerializer(children, many=True, read_only=True).data
    
    def get_content_count(self, obj):
        """Get count of direct contents."""
        return obj.contents.filter(is_active=True).count()


class ContentSerializer(serializers.ModelSerializer):
    """Serializer for Content model."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'slug', 'description', 'body',
            'content_type', 'category', 'category_name', 'tags',
            'image', 'media_url', 'file', 'order',
            'is_active', 'is_featured', 'is_premium',
            'views_count', 'average_rating', 'rating_count',
            'author', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['views_count', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        """Calculate average rating."""
        ratings = obj.ratings.values_list('rating', flat=True)
        if not ratings:
            return None
        return sum(ratings) / len(ratings)
    
    def get_rating_count(self, obj):
        """Get total number of ratings."""
        return obj.ratings.count()


class ContentRatingSerializer(serializers.ModelSerializer):
    """Serializer for ContentRating model."""
    
    class Meta:
        model = ContentRating
        fields = ['id', 'content', 'user_id', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']
