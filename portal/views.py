import hashlib
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from .api import redirect, respond
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from .forms import MissionForm, TestForm, FollowupForm, UserAccessForm, UserForm
from .models import AuditEvent, FollowupEvent, LoginAttempt, Mission, TestRecord
from .security import ROLES, allowed, client_ip, log, visible_missions

LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_LIMITS = (5, 30)


def login_buckets(username, request, now):
    values = ('user:' + username.casefold(), 'ip:' + client_ip(request))
    keys = [hashlib.sha256(value.encode()).hexdigest() for value in values]
    attempts = []
    for key in keys:
        attempt, _ = LoginAttempt.objects.get_or_create(key=key, defaults={'since': now})
        if attempt.since < now - LOGIN_WINDOW:
            attempt.failures, attempt.since = 0, now
            attempt.save(update_fields=['failures', 'since'])
        attempts.append(attempt)
    return keys, attempts


@require_http_methods(['GET', 'POST'])
def login_view(request):
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '')[:150]
        now = timezone.now()
        with transaction.atomic():
            keys, attempts = login_buckets(username, request, now)
            if any(a.failures >= limit for a, limit in zip(attempts, LOGIN_LIMITS)):
                log(request, 'auth.throttled')
                response = respond(request, {'error': 'Trop de tentatives. Réessayez dans 15 minutes.'}, status=429)
                response['Retry-After'] = '900'
                return response
        user = authenticate(request, username=username, password=request.POST.get('password', ''))
        if user:
            login(request, user)
            LoginAttempt.objects.filter(key__in=keys).update(failures=0, since=now)
            log(request, 'auth.login')
            return redirect('dashboard')
        with transaction.atomic():
            _, attempts = login_buckets(username, request, now)
            for attempt in attempts:
                attempt.failures += 1
                attempt.save(update_fields=['failures'])
            log(request, 'auth.failed')
        error = 'Identifiant ou mot de passe incorrect.'
    return respond(request, {'error': error})


@require_POST
def logout_view(request):
    log(request, 'auth.logout')
    logout(request)
    return redirect('login')


@allowed(*ROLES)
def dashboard(request):
    missions = visible_missions(request.user)
    tests = TestRecord.objects.filter(mission__in=missions)
    return respond(request, {'mission_count': missions.count(), 'test_count': tests.count(), 'open_count': tests.exclude(state='resolved').count(), 'critical_count': tests.filter(severity__in=['high', 'critical']).exclude(state='resolved').count(), 'missions': missions.order_by('-created_at')[:5], 'tests': tests.select_related('mission').order_by('-created_at')[:6]})


@allowed(*ROLES)
def tools_view(request):
    tools = [
        ('01', 'Nmap', 'Cartographie réseau', 'Inventaire des hôtes, ports et services. Consignez les paramètres et les résultats du périmètre autorisé.', 'nmap'),
        ('02', 'Metasploit', 'Validation des vulnérabilités', 'Documentez les validations contrôlées, les conditions de test et les mesures de restauration.', 'metasploit'),
        ('03', 'Burp Suite', 'Sécurité applicative', 'Centralisez les observations HTTP et les constats de vos tests web, après suppression des secrets.', 'burp'),
        ('04', 'OWASP ZAP', 'Analyse web', 'Conservez les alertes vérifiées, leur contexte et les preuves issues de vos analyses applicatives.', 'zap'),
    ]
    return respond(request, {'tools': tools})


@allowed(*ROLES)
def missions(request):
    qs = visible_missions(request.user).order_by('-id')
    query = request.GET.get('q', '')[:160]
    if query:
        qs = qs.filter(name__icontains=query)
    return respond(request, {'page': Paginator(qs, 20).get_page(request.GET.get('page')), 'query': query})


@allowed(ROLES[0])
@require_http_methods(['GET', 'POST'])
def mission_create(request):
    form = MissionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            mission = form.save(commit=False)
            mission.created_by = request.user
            mission.save()
            form.save_m2m()
            log(request, 'mission.created', mission.pk, {'authorization': mission.authorization, 'scope': mission.scope, 'members': list(mission.members.values_list('username', flat=True))})
        return redirect('mission', pk=mission.pk)
    return respond(request, {'form': form, 'title': 'Nouvelle mission', 'subtitle': 'Définir l’autorisation, la période et les personnes habilitées.'})


@allowed(*ROLES)
def mission_detail(request, pk):
    mission = get_object_or_404(visible_missions(request.user), pk=pk)
    return respond(request, {'mission': mission, 'tests': mission.tests.select_related('created_by').prefetch_related('followups__actor').order_by('-id')})


def writable(mission):
    return mission.status == 'active' and mission.starts_on <= timezone.localdate() <= mission.ends_on


@allowed(*ROLES[:2])
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def record_test(request, pk):
    mission = get_object_or_404(visible_missions(request.user).select_for_update(), pk=pk)
    if not writable(mission):
        log(request, 'test.rejected', pk, {'reason': 'mission_inactive'})
        return HttpResponse('Mission clôturée ou hors période autorisée.', status=409)
    form = TestForm(request.POST or None, mission=mission)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.mission, record.created_by = mission, request.user
        record.evidence_sha256 = hashlib.sha256(record.evidence.encode('utf-8')).hexdigest()
        record.save()
        log(request, 'test.recorded', record.pk, {'mission': pk, 'tool': record.tool, 'target': record.target, 'sha256': record.evidence_sha256})
        return redirect('mission', pk=pk)
    if request.method == 'POST':
        log(request, 'test.rejected', pk, {'fields': list(form.errors)})
    return respond(request, {'form': form, 'title': 'Documenter un test', 'subtitle': mission.name + ' · Résultats d’un test exécuté hors de cette interface.'})


@allowed(*ROLES[:2])
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def update_finding(request, pk):
    record = get_object_or_404(TestRecord.objects.select_for_update().filter(mission__in=visible_missions(request.user)), pk=pk)
    if record.mission.status != 'active':
        return HttpResponse('Réouvrez la mission avant de modifier le suivi.', status=409)
    before = record.state
    form = FollowupForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        FollowupEvent.objects.create(record=record, state=record.state, retest=record.retest, actor=request.user)
        log(request, 'finding.updated', pk, {'before': before, 'after': record.state, 'retest': record.retest})
        return redirect('mission', pk=record.mission_id)
    return respond(request, {'form': form, 'title': 'Suivi de correction', 'subtitle': record.title})


@allowed(ROLES[0])
@require_POST
@transaction.atomic
def mission_status(request, pk):
    mission = get_object_or_404(Mission.objects.select_for_update(), pk=pk)
    mission.status = 'closed' if mission.status == 'active' else 'active'
    mission.save(update_fields=['status'])
    log(request, 'mission.status', pk, {'status': mission.status})
    return redirect('mission', pk=pk)


@allowed(*ROLES)
def report(request, pk):
    mission = get_object_or_404(visible_missions(request.user), pk=pk)
    records = list(mission.tests.select_related('created_by').prefetch_related('followups__actor').order_by('id'))
    log(request, 'report.exported', pk)
    data = {'schema': 'audit-hub.report.v2', 'exported_at': timezone.now().isoformat(), 'notice': 'Éléments de preuve techniques ; ne constitue pas une certification ISO 27001.', 'mission': {'id': pk, 'name': mission.name, 'authorization': mission.authorization, 'scope': mission.scope.splitlines(), 'starts_on': mission.starts_on, 'ends_on': mission.ends_on, 'status': mission.status}, 'controls': ['A.8.8', 'A.8.25', 'A.8.29'], 'tests': [{**{f: getattr(r, f) for f in ('id', 'tool', 'tool_version', 'target', 'title', 'performed_at', 'method', 'evidence', 'evidence_sha256', 'severity', 'remediation', 'owner', 'due_on', 'state', 'retest', 'created_at')}, 'author': r.created_by.username, 'followups': [{'state': event.state, 'retest': event.retest, 'actor': event.actor.username, 'created_at': event.created_at} for event in r.followups.all()]} for r in records]}
    response = JsonResponse(data, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="mission-{pk}.json"'
    return response


@allowed(ROLES[0], ROLES[2])
def journal(request):
    # Auditors see only their own events; the global journal is reserved to administrators.
    events = AuditEvent.objects.all()
    if not (request.user.is_superuser or request.user.groups.filter(name=ROLES[0]).exists()):
        events = events.filter(actor=request.user.username)
    action = request.GET.get('action', '')[:80]
    if action:
        events = events.filter(action__icontains=action)
    return respond(request, {'page': Paginator(events, 50).get_page(request.GET.get('page')), 'action': action})


@allowed(ROLES[0])
def export_journal(request):
    log(request, 'journal.exported')
    response = JsonResponse({'schema': 'audit-hub.events.v1', 'events': list(AuditEvent.objects.order_by('id').values())}, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="journal-audit.json"'
    return response


@allowed(ROLES[0])
@require_http_methods(['GET', 'POST'])
def users(request):
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = get_user_model().objects.create_user(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            group, _ = Group.objects.get_or_create(name=form.cleaned_data['role'])
            user.groups.add(group)
            log(request, 'user.created', user.pk, {'username': user.username, 'role': group.name})
        return redirect('users')
    return respond(request, {'form': form, 'users': get_user_model().objects.prefetch_related('groups').order_by('username')})


@allowed(ROLES[0])
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def user_access(request, pk):
    user = get_object_or_404(get_user_model().objects.select_for_update(), pk=pk, is_superuser=False)
    current_role = next((name for name in ROLES if user.groups.filter(name=name).exists()), ROLES[2])
    initial = {'role': current_role, 'status': 'active' if user.is_active else 'disabled'}
    form = UserAccessForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        if user == request.user and (form.cleaned_data['status'] == 'disabled' or form.cleaned_data['role'] != ROLES[0]):
            form.add_error(None, 'Vous ne pouvez pas révoquer vos propres droits administrateur.')
        else:
            group, _ = Group.objects.get_or_create(name=form.cleaned_data['role'])
            user.groups.set([group])
            user.is_active = form.cleaned_data['status'] == 'active'
            user.save(update_fields=['is_active'])
            log(request, 'user.access_changed', user.pk, {'username': user.username, 'role': group.name, 'active': user.is_active, 'reason': form.cleaned_data['reason']})
            return redirect('users')
    return respond(request, {'form': form, 'title': 'Gérer ' + user.username, 'subtitle': 'Modifier le rôle ou révoquer l’accès avec un motif obligatoire.'})


@allowed(*ROLES)
def compliance(request):
    return respond(request)
