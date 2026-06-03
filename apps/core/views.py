"""Core app views."""
from django.shortcuts import redirect
from django.http import JsonResponse


def homepage(request):
    """Redirect to admin panel."""
    return redirect('admin:index')


def api_root(request):
    """API root information."""
    return JsonResponse({
        'message': 'ContentMentor API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'categories': '/api/categories/',
            'content': '/api/content/',
            'access_control': '/api/check-access/',
        },
        'bot': {
            'name': '@kidsgenius_bot',
            'platform': 'Telegram',
        }
    })
