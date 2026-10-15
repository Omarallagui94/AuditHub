from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from portal.models import AuditEvent
from portal.security import ROLES


class Command(BaseCommand):
    help = 'Changer un rôle ou désactiver un compte avec une trace d’administration.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--role', choices=ROLES)
        parser.add_argument('--disable', action='store_true')
        parser.add_argument('--enable', action='store_true')
        parser.add_argument('--reason', required=True)

    @transaction.atomic
    def handle(self, *args, **opts):
        try:
            user = get_user_model().objects.get(username=opts['username'])
        except get_user_model().DoesNotExist:
            raise CommandError('Compte introuvable.')
        if user.is_superuser:
            raise CommandError('Cette commande ne modifie pas les superutilisateurs.')
        if opts['disable'] and opts['enable']:
            raise CommandError('Choisissez --enable ou --disable.')
        if not (opts['role'] or opts['disable'] or opts['enable']):
            raise CommandError('Indiquez une modification.')
        if opts['role']:
            group, _ = Group.objects.get_or_create(name=opts['role'])
            user.groups.set([group])
        if opts['disable'] or opts['enable']:
            user.is_active = opts['enable']
            user.save(update_fields=['is_active'])
        AuditEvent.objects.create(actor='console-admin', action='user.access_changed', object_ref=str(user.pk), ip='local', detail={'username': user.username, 'role': opts['role'], 'active': user.is_active, 'reason': opts['reason']})
        self.stdout.write(self.style.SUCCESS('Accès mis à jour et journalisé.'))
