from django.conf import settings
from django.db import models


class Mission(models.Model):
    name = models.CharField(max_length=160)
    authorization = models.CharField(max_length=240)
    scope = models.TextField(help_text='Une adresse IP ou un réseau CIDR par ligne.')
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=12, default='active', choices=[('active', 'Active'), ('closed', 'Clôturée')])
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='missions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(ends_on__gte=models.F('starts_on')), name='mission_dates_in_order')]


class TestRecord(models.Model):
    TOOLS = [('nmap', 'Nmap'), ('metasploit', 'Metasploit'), ('burp', 'Burp Suite'), ('zap', 'OWASP ZAP')]
    SEVERITIES = [('info', 'Information'), ('low', 'Faible'), ('medium', 'Moyenne'), ('high', 'Élevée'), ('critical', 'Critique')]
    STATES = [('open', 'Ouvert'), ('progress', 'En correction'), ('resolved', 'Résolu')]
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT, related_name='tests')
    tool = models.CharField(max_length=20, choices=TOOLS)
    tool_version = models.CharField(max_length=80)
    target = models.GenericIPAddressField()
    title = models.CharField(max_length=200)
    method = models.TextField()
    evidence = models.TextField()
    evidence_sha256 = models.CharField(max_length=64)
    severity = models.CharField(max_length=10, choices=SEVERITIES)
    remediation = models.TextField()
    owner = models.CharField(max_length=160)
    due_on = models.DateField()
    state = models.CharField(max_length=12, choices=STATES, default='open')
    retest = models.TextField(blank=True)
    performed_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=~models.Q(state='resolved') | ~models.Q(retest=''), name='resolved_requires_retest')]


class FollowupEvent(models.Model):
    record = models.ForeignKey(TestRecord, on_delete=models.PROTECT, related_name='followups')
    state = models.CharField(max_length=12, choices=TestRecord.STATES)
    retest = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']


class AuditEvent(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=150)
    action = models.CharField(max_length=80)
    object_ref = models.CharField(max_length=120, blank=True)
    detail = models.JSONField(default=dict)
    ip = models.CharField(max_length=64)

    class Meta:
        ordering = ['-id']


class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    since = models.DateTimeField()
