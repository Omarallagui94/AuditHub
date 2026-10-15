from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from portal.models import LoginAttempt


class Command(BaseCommand):
    help = 'Supprimer les fenêtres de limitation de connexion expirées.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-minutes', type=int, default=15)

    def handle(self, *args, **options):
        minutes = options['older_than_minutes']
        if minutes < 15:
            raise CommandError('La conservation minimale est de 15 minutes.')
        cutoff = timezone.now() - timedelta(minutes=minutes)
        deleted, _ = LoginAttempt.objects.filter(since__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'{deleted} tentative(s) expirée(s) supprimée(s).'))
