# authentification/middleware.py
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django_otp.plugins.otp_totp.models import TOTPDevice

class TwoFactorMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # Exclure les URLs de configuration 2FA
            if request.path in [reverse('setup_2fa')]:
                return
            
            # Vérifier si la 2FA est configurée mais non validée
            has_2fa = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
            if has_2fa and not request.session.get('2fa_verified'):
                return HttpResponseRedirect(reverse('verify_2fa'))
            

from django.utils.deprecation import MiddlewareMixin
from rest_framework.authtoken.models import Token

class TokenCleanupMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Nettoyage préventif des tokens multiples
        if request.user.is_authenticated:
            tokens = Token.objects.filter(user=request.user)
            if tokens.count() > 1:
                # Garde le token le plus récent
                tokens.exclude(pk=tokens.latest('created').pk).delete()