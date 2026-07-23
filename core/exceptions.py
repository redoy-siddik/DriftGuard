import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """DRF custom exception handler — wraps all errors in consistent envelope."""
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': True,
            'status_code': response.status_code,
            'detail': response.data,
        }
    else:
        logger.exception(f"Unhandled exception in {context.get('view')}: {exc}")
    return response


def handler404(request, exception):
    if request.path.startswith('/api/'):
        return JsonResponse({'error': True, 'status_code': 404, 'detail': 'Not found.'}, status=404)
    from django.shortcuts import render
    return render(request, '404.html', status=404)


def handler500(request):
    if request.path.startswith('/api/'):
        return JsonResponse({'error': True, 'status_code': 500, 'detail': 'Internal server error.'}, status=500)
    from django.shortcuts import render
    return render(request, '500.html', status=500)
