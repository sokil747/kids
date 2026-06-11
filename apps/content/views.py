"""Content API views."""
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Tag, Category, Content, ContentRating, Business
from .serializers import TagSerializer, CategorySerializer, ContentSerializer, ContentRatingSerializer, BusinessSerializer


class TagsList(generics.ListAPIView):
    """Get all active tags."""
    queryset = Tag.objects.filter(is_active=True).order_by('order')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class CategoriesList(generics.ListCreateAPIView):
    """Get all active categories or create new one."""
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return only active main categories."""
        return Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).order_by('order')


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """Get, update or delete a category."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CategoryContents(generics.ListAPIView):
    """Get all contents in a category."""
    serializer_class = ContentSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        category_id = self.kwargs['pk']
        return Content.objects.filter(
            category_id=category_id,
            is_active=True
        ).order_by('-is_featured', 'order')


class ContentList(generics.ListCreateAPIView):
    """Get all active contents or create new one."""
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return only active contents."""
        return Content.objects.filter(is_active=True).order_by('-is_featured', '-created_at')


class ContentDetail(generics.RetrieveUpdateDestroyAPIView):
    """Get, update or delete content."""
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count on retrieval."""
        response = super().retrieve(request, *args, **kwargs)
        obj = self.get_object()
        obj.increment_views()
        return response


class RateContent(generics.CreateAPIView):
    """Rate a content item."""
    serializer_class = ContentRatingSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create or update rating."""
        content_id = self.kwargs['pk']
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rating_obj, created = ContentRating.objects.update_or_create(
            content_id=content_id,
            user_id=user_id,
            defaults={
                'rating': request.data.get('rating', 5),
                'comment': request.data.get('comment', '')
            }
        )
        
        serializer = self.get_serializer(rating_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BusinessList(generics.ListAPIView):
    """Get all active businesses."""
    serializer_class = BusinessSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Business.objects.filter(is_active=True).order_by('order', '-created_at')


class BusinessDetail(generics.RetrieveAPIView):
    """Get a single business by ID."""
    serializer_class = BusinessSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Business.objects.filter(is_active=True)


class BusinessByCategory(generics.ListAPIView):
    """Get businesses for a specific category."""
    serializer_class = BusinessSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category_id = self.kwargs['pk']
        return Business.objects.filter(
            categories__id=category_id,
            is_active=True
        ).order_by('order', '-created_at')
