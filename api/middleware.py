from django.utils import timezone
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

class TokenExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request, 'auth'):
            token_key = request.auth.key if request.auth else None
            if token_key:
                try:
                    token = Token.objects.get(key=token_key)
                    time_elapsed = (timezone.now() - token.created).total_seconds()
                    if time_elapsed > settings.REST_FRAMEWORK_TOKEN_EXPIRE:
                        logger.info(f"Token expired for user {request.user.username}")
                        token.delete()
                        return HttpResponseRedirect(settings.SESSION_TIMEOUT_REDIRECT)
                except Token.DoesNotExist:
                    logger.warning(f"Invalid token for user {request.user.username}")
                    return HttpResponseRedirect(settings.SESSION_TIMEOUT_REDIRECT)
        response = self.get_response(request)
        return response