from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from .models import AuditEvent, Mission

ROLES = ('Administrateur', 'Pentesteur', 'Auditeur')


def client_ip(request):
    """Return a proxy-validated client address, or the direct peer address."""
    if getattr(settings, 'TRUST_PROXY_HEADERS', False):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',', 1)[0].strip()[:64]
    return request.META.get('REMOTE_ADDR', '')[:64]


def role(user):
    if not user.is_authenticated:
        return ''
    if user.is_superuser:
        return ROLES[0]
    return next((r for r in ROLES if user.groups.filter(name=r).exists()), '')


def log(request, action, obj='', detail=None):
    return AuditEvent.objects.create(actor=request.user.username if request.user.is_authenticated else 'anonyme', action=action, object_ref=str(obj), detail=detail or {}, ip=client_ip(request))


def allowed(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Veuillez vous connecter.'}, status=401)
            if role(request.user) not in roles:
                log(request, 'access.denied', request.path)
                request._access_denial_logged = True
                return JsonResponse({'error': 'Accès refusé pour ce rôle.'}, status=403)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def visible_missions(user):
    return Mission.objects.all() if role(user) == ROLES[0] else Mission.objects.filter(members=user)


def context(request):
    r = role(request.user)
    return {'current_role': r, 'is_manager': r == ROLES[0], 'can_write': r in ROLES[:2]}


class HeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response['Cache-Control'] = 'no-store'
        if response.status_code == 403 and not getattr(request, '_access_denial_logged', False):
            log(request, 'http.forbidden', request.path)
        return response
