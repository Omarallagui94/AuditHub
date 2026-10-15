import ipaddress
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils import timezone
from .models import Mission, TestRecord
from .security import ROLES


class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['name', 'authorization', 'scope', 'starts_on', 'ends_on', 'members']
        labels = {'name': 'Nom de la mission', 'authorization': 'Référence de l’autorisation écrite', 'scope': 'Périmètre autorisé (IP / CIDR)', 'starts_on': 'Début', 'ends_on': 'Fin', 'members': 'Utilisateurs habilités'}
        widgets = {'starts_on': forms.DateInput(attrs={'type': 'date'}), 'ends_on': forms.DateInput(attrs={'type': 'date'}), 'scope': forms.Textarea(attrs={'rows': 4})}

    def clean_scope(self):
        lines = self.cleaned_data['scope'].splitlines()
        try:
            networks = [str(ipaddress.ip_network(s.strip(), strict=False)) for s in lines if s.strip()]
        except ValueError:
            raise ValidationError('Utilisez uniquement des adresses IP ou réseaux CIDR valides.')
        if not networks or len(networks) > 100:
            raise ValidationError('Le périmètre doit contenir entre 1 et 100 entrées.')
        return '\n'.join(networks)

    def clean(self):
        data = super().clean()
        if data.get('starts_on') and data.get('ends_on') and data['ends_on'] < data['starts_on']:
            self.add_error('ends_on', 'La fin doit suivre le début.')
        return data


class TestForm(forms.ModelForm):
    class Meta:
        model = TestRecord
        fields = ['tool', 'tool_version', 'target', 'title', 'performed_at', 'method', 'evidence', 'severity', 'remediation', 'owner', 'due_on']
        labels = {'tool': 'Outil', 'tool_version': 'Version utilisée', 'target': 'IP de la cible', 'title': 'Titre du constat', 'performed_at': 'Date du test (heure de Lagos)', 'method': 'Méthode et paramètres', 'evidence': 'Preuve textuelle expurgée des secrets', 'severity': 'Sévérité', 'remediation': 'Mesure corrective', 'owner': 'Responsable de correction', 'due_on': 'Échéance'}
        widgets = {'performed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}), 'due_on': forms.DateInput(attrs={'type': 'date'}), 'method': forms.Textarea(attrs={'rows': 3}), 'evidence': forms.Textarea(attrs={'rows': 5}), 'remediation': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, mission, **kwargs):
        super().__init__(*args, **kwargs)
        self.mission = mission
        for name in ('method', 'evidence', 'remediation'):
            self.fields[name].max_length = 20000
            self.fields[name].validators.append(MaxLengthValidator(20000))

    def clean_target(self):
        target = self.cleaned_data['target']
        if not any(ipaddress.ip_address(target) in ipaddress.ip_network(n) for n in self.mission.scope.splitlines()):
            raise ValidationError('Cette cible est hors du périmètre autorisé.')
        return target

    def clean_performed_at(self):
        value = self.cleaned_data['performed_at']
        if value > timezone.now() or not self.mission.starts_on <= timezone.localtime(value).date() <= self.mission.ends_on:
            raise ValidationError('La date doit être passée et comprise dans la période autorisée.')
        return value


class FollowupForm(forms.ModelForm):
    class Meta:
        model = TestRecord
        fields = ['state', 'retest']
        labels = {'state': 'État', 'retest': 'Preuve de re-test / commentaire de suivi'}
        widgets = {'retest': forms.Textarea(attrs={'rows': 3, 'maxlength': 20000})}

    def clean(self):
        data = super().clean()
        if data.get('state') == 'resolved' and not data.get('retest', '').strip():
            self.add_error('retest', 'Une preuve de re-test est nécessaire pour résoudre un constat.')
        if len(data.get('retest', '')) > 20000:
            self.add_error('retest', '20 000 caractères maximum.')
        return data


class UserForm(forms.Form):
    username = forms.CharField(label='Identifiant', max_length=150)
    password = forms.CharField(label='Mot de passe initial', widget=forms.PasswordInput)
    role = forms.ChoiceField(label='Rôle', choices=[(x, x) for x in ROLES])

    def clean(self):
        data = super().clean()
        if data.get('username'):
            user = get_user_model()(username=data['username'])
            try:
                user.full_clean(exclude=['password', 'last_login', 'date_joined'])
                if data.get('password'):
                    validate_password(data['password'], user)
            except ValidationError as exc:
                raise ValidationError(exc.messages)
        return data


class UserAccessForm(forms.Form):
    role = forms.ChoiceField(label='Rôle', choices=[(x, x) for x in ROLES])
    status = forms.ChoiceField(label='État du compte', choices=[('active', 'Actif'), ('disabled', 'Désactivé')])
    reason = forms.CharField(label='Motif du changement', max_length=500, widget=forms.Textarea(attrs={'rows': 3}))
