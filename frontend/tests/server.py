"""Isolated browser-test server. Never connects to the user's database."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ['AUDIT_DEV'] = '1'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
from django.conf import settings

with tempfile.TemporaryDirectory(prefix='audithub-e2e-') as directory:
    settings.DATABASES['default']['NAME'] = str(Path(directory) / 'tests.sqlite3')
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.core.management import call_command
    from portal.security import ROLES
    call_command('migrate', verbosity=0)
    for username, role in zip(('admin-test', 'tester-test', 'auditor-test'), ROLES):
        user = get_user_model().objects.create_user(username=username, password='Browser-Tests-Only!294')
        user.groups.add(Group.objects.create(name=role))
    call_command('runserver', '127.0.0.1:8765', use_reloader=False)
