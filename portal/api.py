"""JSON presentation layer, with business validation retained in Django forms."""
from django import forms
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.db.models import QuerySet
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render as template_render
from django.urls import reverse
from django.views.decorators.http import require_GET
from .models import Mission, TestRecord, AuditEvent
from .security import role, context


def serialize(value):
    if isinstance(value, get_user_model()):
        return {'id': value.pk, 'username': value.username, 'role': role(value), 'is_active': value.is_active, 'is_superuser': value.is_superuser}
    if isinstance(value, Mission):
        return {'id': value.pk, 'name': value.name, 'authorization': value.authorization, 'scope': value.scope, 'starts_on': value.starts_on, 'ends_on': value.ends_on, 'status': value.status, 'status_label': value.get_status_display()}
    if isinstance(value, TestRecord):
        data = model_to_dict(value, exclude=['created_by'])
        data.update(
            author=value.created_by.username,
            created_at=value.created_at,
            tool_label=value.get_tool_display(),
            state_label=value.get_state_display(),
            severity_label=value.get_severity_display(),
            followups=[{'state': event.state, 'state_label': event.get_state_display(), 'retest': event.retest, 'actor': event.actor.username, 'created_at': event.created_at} for event in value.followups.all()],
        )
        return data
    if isinstance(value, AuditEvent):
        return {'id': value.pk, 'timestamp': value.timestamp, 'actor': value.actor, 'action': value.action, 'object_ref': value.object_ref, 'detail': value.detail, 'ip': value.ip}
    if isinstance(value, forms.BaseForm):
        fields = []
        for name, field in value.fields.items():
            bound = value[name]
            widget = field.widget
            multiple = isinstance(widget, forms.SelectMultiple)
            kind = 'textarea' if isinstance(widget, forms.Textarea) else 'select' if isinstance(widget, forms.Select) else getattr(widget, 'input_type', 'text')
            initial = None if kind == 'password' else bound.value()
            if isinstance(initial, QuerySet):
                initial = list(initial.values_list('pk', flat=True))
            choices = [{'value': str(k), 'label': str(v)} for k, v in field.choices] if hasattr(field, 'choices') else []
            fields.append({'name': name, 'label': str(bound.label), 'type': kind, 'multiple': multiple, 'required': field.required, 'help': str(field.help_text), 'maxLength': getattr(field, 'max_length', None), 'value': initial, 'choices': choices, 'errors': list(bound.errors)})
        return {'fields': fields, 'errors': list(value.non_field_errors())}
    if isinstance(value, Page):
        return {'items': serialize(list(value)), 'number': value.number, 'pages': value.paginator.num_pages, 'count': value.paginator.count}
    if isinstance(value, (list, tuple, QuerySet)):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    return value


def respond(request, data=None, status=200):
    data = data or {}
    if request.method == 'POST' and data.get('form') is not None and data['form'].errors:
        status = 422
    if request.method == 'POST' and data.get('error') and status == 200:
        status = 401
    return JsonResponse(serialize(data), status=status, json_dumps_params={'ensure_ascii': False})


def redirect(name, **kwargs):
    return JsonResponse({'redirect': reverse(name, kwargs=kwargs).removeprefix('/api') or '/'})


@require_GET
def session(request):
    return JsonResponse({'user': serialize(request.user) if request.user.is_authenticated else None, 'csrfToken': get_token(request), **context(request)})


@require_GET
def shell(request, **kwargs):
    return template_render(request, 'app.html')


def csrf_failure(request, reason=''):
    return JsonResponse({'error': 'Session de formulaire expirée. Rechargez la page puis réessayez.'}, status=403)


class ErrorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/') and response.status_code >= 400 and not response.get('Content-Type', '').startswith('application/json'):
            errors = {403: 'Accès refusé.', 404: 'Ressource introuvable ou non autorisée.', 405: 'Méthode non autorisée.', 409: 'Mission clôturée ou hors période autorisée.', 500: 'Une erreur serveur est survenue.'}
            return JsonResponse({'error': errors.get(response.status_code, 'La requête a échoué.')}, status=response.status_code)
        return response
