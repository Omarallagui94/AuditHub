from datetime import timedelta
import hashlib
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import AuditEvent, FollowupEvent, LoginAttempt, Mission, TestRecord
from .security import ROLES


@override_settings(SECURE_SSL_REDIRECT=False)
class SecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.people = []
        for index, role in enumerate(ROLES):
            user = get_user_model().objects.create_user(username=f'user{index}', password='Strong-Test-Password!28')
            user.groups.add(Group.objects.create(name=role))
            cls.people.append(user)
        cls.admin, cls.tester, cls.auditor = cls.people
        cls.outsider = get_user_model().objects.create_user(username='outsider', password='Strong-Test-Password!28')
        cls.outsider.groups.add(Group.objects.get(name=ROLES[1]))
        cls.mission = Mission.objects.create(name='Audit laboratoire', authorization='AUT-004', scope='192.0.2.0/24', starts_on=timezone.localdate()-timedelta(days=1), ends_on=timezone.localdate()+timedelta(days=7), created_by=cls.admin)
        cls.mission.members.add(cls.tester, cls.auditor)

    def payload(self):
        return {'tool': 'nmap', 'tool_version': '7.95', 'target': '192.0.2.10', 'title': 'Service à examiner', 'performed_at': (timezone.now()-timedelta(minutes=5)).isoformat(), 'method': 'Inventaire contrôlé', 'evidence': '<script>alert(1)</script>', 'severity': 'medium', 'remediation': 'Vérifier le service', 'owner': 'Équipe réseau', 'due_on': (timezone.localdate()+timedelta(days=3)).isoformat()}

    def add_record(self):
        self.client.force_login(self.tester)
        response = self.client.post(reverse('record_test', args=[self.mission.pk]), self.payload())
        self.assertEqual(response.status_code, 200)
        return TestRecord.objects.get()

    def test_anonymous_api_access_denied(self):
        for url in ('/api/', '/api/missions/', '/api/outils/', '/api/journal/', '/api/utilisateurs/'):
            self.assertEqual(self.client.get(url).status_code, 401)

    def test_all_authorized_pages_render(self):
        self.client.force_login(self.admin)
        for name in ('dashboard', 'missions', 'tools', 'journal', 'users', 'compliance', 'mission_create'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse('mission', args=[self.mission.pk])).status_code, 200)

    def test_auditor_cannot_write(self):
        self.client.force_login(self.auditor)
        for url in (reverse('record_test', args=[self.mission.pk]), reverse('mission_status', args=[self.mission.pk]), reverse('mission_create'), reverse('users')):
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
        self.assertFalse(TestRecord.objects.exists())

    def test_cross_mission_access_denied(self):
        self.client.force_login(self.outsider)
        for name in ('mission', 'report', 'record_test'):
            self.assertEqual(self.client.get(reverse(name, args=[self.mission.pk])).status_code, 404)

    def test_user_without_role_denied(self):
        user = get_user_model().objects.create_user(username='unassigned')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/api/').status_code, 403)

    def test_out_of_scope_target_rejected(self):
        self.client.force_login(self.tester)
        data = self.payload()
        data['target'] = '198.51.100.1'
        self.assertContains(self.client.post(reverse('record_test', args=[self.mission.pk]), data), 'hors du périmètre', status_code=422)
        self.assertFalse(TestRecord.objects.exists())

    def test_command_as_target_rejected(self):
        self.client.force_login(self.tester)
        data = self.payload()
        data['target'] = '192.0.2.1; whoami'
        self.client.post(reverse('record_test', args=[self.mission.pk]), data)
        self.assertFalse(TestRecord.objects.exists())

    def test_closed_and_expired_mission_rejected(self):
        self.client.force_login(self.tester)
        self.mission.status = 'closed'
        self.mission.save()
        self.assertEqual(self.client.post(reverse('record_test', args=[self.mission.pk]), self.payload()).status_code, 409)
        self.mission.status = 'active'
        self.mission.ends_on = timezone.localdate()-timedelta(days=1)
        self.mission.save()
        self.assertEqual(self.client.post(reverse('record_test', args=[self.mission.pk]), self.payload()).status_code, 409)

    def test_evidence_hash_and_transaction_log(self):
        record = self.add_record()
        self.assertEqual(record.evidence_sha256, hashlib.sha256(self.payload()['evidence'].encode()).hexdigest())
        self.assertTrue(AuditEvent.objects.filter(action='test.recorded', object_ref=str(record.pk)).exists())

    def test_evidence_delivered_as_json_not_html(self):
        self.add_record()
        response = self.client.get(reverse('mission', args=[self.mission.pk]))
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['tests'][0]['evidence'], '<script>alert(1)</script>')

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse('mission_status', args=[self.mission.pk])).status_code, 403)
        self.assertEqual(client.post(reverse('login'), {'username': 'user0', 'password': 'x'}).status_code, 403)

    def test_logout_and_status_require_post(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertEqual(self.client.get(reverse('mission_status', args=[self.mission.pk])).status_code, 405)

    def test_resolution_requires_retest(self):
        record = self.add_record()
        url = reverse('update_finding', args=[record.pk])
        self.client.post(url, {'state': 'resolved', 'retest': ''})
        record.refresh_from_db()
        self.assertEqual(record.state, 'open')
        self.assertEqual(self.client.post(url, {'state': 'resolved', 'retest': 'Contrôle de validation effectué.'}).status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.state, 'resolved')
        self.assertEqual(FollowupEvent.objects.filter(record=record).count(), 1)

    def test_report_preserves_followup_history(self):
        record = self.add_record()
        url = reverse('update_finding', args=[record.pk])
        self.client.post(url, {'state': 'progress', 'retest': 'Correction en cours.'})
        self.client.post(url, {'state': 'resolved', 'retest': 'Correction validée.'})
        report = self.client.get(reverse('report', args=[self.mission.pk])).json()
        self.assertEqual(report['schema'], 'audit-hub.report.v2')
        self.assertEqual([item['state'] for item in report['tests'][0]['followups']], ['progress', 'resolved'])

    def test_database_constraints_reject_invalid_state(self):
        record = self.add_record()
        with self.assertRaises(IntegrityError), transaction.atomic():
            TestRecord.objects.filter(pk=record.pk).update(state='resolved', retest='')

    def test_report_contains_evidence_and_logs_export(self):
        self.add_record()
        self.client.force_login(self.auditor)
        response = self.client.get(reverse('report', args=[self.mission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['tests'][0]['target'], '192.0.2.10')
        self.assertTrue(AuditEvent.objects.filter(action='report.exported', actor=self.auditor.username).exists())

    def test_global_journal_restricted(self):
        self.client.force_login(self.auditor)
        self.assertEqual(self.client.get(reverse('export_journal')).status_code, 403)
        AuditEvent.objects.create(actor=self.admin.username, action='hidden.private.event', ip='local')
        self.assertNotContains(self.client.get(reverse('journal')), 'hidden.private.event')

    def test_login_throttle(self):
        for _ in range(5):
            self.assertEqual(self.client.post(reverse('login'), {'username': 'user1', 'password': 'wrong'}).status_code, 401)
        self.assertEqual(self.client.post(reverse('login'), {'username': 'user1', 'password': 'Strong-Test-Password!28'}).status_code, 429)
        self.assertEqual(AuditEvent.objects.filter(action='auth.failed').count(), 5)

    def test_login_success_and_logout(self):
        response = self.client.post(reverse('login'), {'username': 'user1', 'password': 'Strong-Test-Password!28'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(action='auth.login', actor='user1').exists())
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get('/api/').status_code, 401)

    def test_successful_logins_do_not_exhaust_shared_ip_bucket(self):
        for _ in range(31):
            response = self.client.post(reverse('login'), {'username': 'user1', 'password': 'Strong-Test-Password!28'}, REMOTE_ADDR='192.0.2.50')
            self.assertEqual(response.status_code, 200)
            self.client.post(reverse('logout'), REMOTE_ADDR='192.0.2.50')

    @override_settings(TRUST_PROXY_HEADERS=True)
    def test_trusted_proxy_client_ip_is_used(self):
        self.client.post(reverse('login'), {'username': 'missing', 'password': 'wrong'}, REMOTE_ADDR='127.0.0.1', HTTP_X_FORWARDED_FOR='198.51.100.8')
        self.assertEqual(AuditEvent.objects.filter(action='auth.failed').latest('id').ip, '198.51.100.8')

    def test_expired_login_attempts_can_be_purged(self):
        LoginAttempt.objects.create(key='expired', failures=1, since=timezone.now() - timedelta(minutes=16))
        call_command('purge_login_attempts')
        self.assertFalse(LoginAttempt.objects.filter(key='expired').exists())

    def test_security_headers(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn("script-src 'self'", response['Content-Security-Policy'])
        self.assertNotIn("'unsafe-inline'", response['Content-Security-Policy'])
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_weak_password_rejected(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('users'), {'username': 'newuser', 'password': '123', 'role': ROLES[1]})
        self.assertFalse(get_user_model().objects.filter(username='newuser').exists())

    def test_create_account_password_hashed(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('users'), {'username': 'newuser', 'password': 'Long-New-Password!83', 'role': ROLES[1]})
        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username='newuser')
        self.assertNotEqual(user.password, 'Long-New-Password!83')
        self.assertTrue(user.check_password('Long-New-Password!83'))
        self.assertFalse(user.is_superuser)

    def test_admin_can_change_role_and_disable_account(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('user_access', args=[self.tester.pk]), {'role': ROLES[2], 'status': 'disabled', 'reason': 'Fin de mission'})
        self.assertEqual(response.status_code, 200)
        self.tester.refresh_from_db()
        self.assertFalse(self.tester.is_active)
        self.assertTrue(self.tester.groups.filter(name=ROLES[2]).exists())
        self.assertTrue(AuditEvent.objects.filter(action='user.access_changed', object_ref=str(self.tester.pk)).exists())

    def test_admin_cannot_disable_self(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('user_access', args=[self.admin.pk]), {'role': ROLES[0], 'status': 'disabled', 'reason': 'Erreur'})
        self.assertEqual(response.status_code, 422)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_future_test_date_rejected(self):
        self.client.force_login(self.tester)
        data = self.payload()
        data['performed_at'] = (timezone.now()+timedelta(days=1)).isoformat()
        self.client.post(reverse('record_test', args=[self.mission.pk]), data)
        self.assertFalse(TestRecord.objects.exists())

    def test_react_shell_and_deep_links(self):
        for url in ('/', '/connexion/', '/missions/123/', '/tests/123/suivi/'):
            response = self.client.get(url)
            self.assertContains(response, 'id="root"')
            self.assertContains(response, '/static/react/app.js')

    def test_session_csrf_rotation_and_protected_post(self):
        client = Client(enforce_csrf_checks=True)
        initial = client.get('/api/session/').json()
        self.assertIsNone(initial['user'])
        response = client.post('/api/connexion/', {'username': 'user0', 'password': 'Strong-Test-Password!28'}, HTTP_X_CSRFTOKEN=initial['csrfToken'])
        self.assertEqual(response.status_code, 200)
        authenticated = client.get('/api/session/').json()
        self.assertEqual(authenticated['user']['username'], 'user0')
        self.assertNotIn('password', authenticated['user'])
        self.assertNotEqual(initial['csrfToken'], authenticated['csrfToken'])
        self.assertEqual(client.post('/api/deconnexion/', HTTP_X_CSRFTOKEN=authenticated['csrfToken']).status_code, 200)
        self.assertIsNone(client.get('/api/session/').json()['user'])

    def test_form_schema_excludes_passwords(self):
        self.client.force_login(self.admin)
        response = self.client.post('/api/utilisateurs/', {'username': 'newuser', 'password': 'short', 'role': ROLES[1]})
        self.assertEqual(response.status_code, 422)
        field = next(f for f in response.json()['form']['fields'] if f['name'] == 'password')
        self.assertIsNone(field['value'])
        self.assertNotIn('password', response.json()['users'][0])

    def test_mission_creation_through_api(self):
        self.client.force_login(self.admin)
        response = self.client.post('/api/missions/nouvelle/', {'name': 'API Mission', 'authorization': 'AUT-API', 'scope': '192.0.2.0/24', 'starts_on': timezone.localdate(), 'ends_on': timezone.localdate(), 'members': [self.tester.pk, self.auditor.pk]})
        self.assertEqual(response.status_code, 200)
        mission = Mission.objects.get(name='API Mission')
        self.assertEqual(mission.members.count(), 2)
        self.assertEqual(response.json()['redirect'], f'/missions/{mission.pk}/')

    def test_api_errors_are_json(self):
        self.client.force_login(self.admin)
        for url in ('/api/missions/9999/', '/api/unknown/', '/api/deconnexion/'):
            self.assertEqual(self.client.get(url)['Content-Type'], 'application/json')
