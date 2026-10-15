import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('portal', '0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='FollowupEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('open', 'Ouvert'), ('progress', 'En correction'), ('resolved', 'Résolu')], max_length=12)),
                ('retest', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='followups', to='portal.testrecord')),
            ],
            options={'ordering': ['id']},
        ),
        migrations.AddConstraint(model_name='mission', constraint=models.CheckConstraint(condition=models.Q(ends_on__gte=models.F('starts_on')), name='mission_dates_in_order')),
        migrations.AddConstraint(model_name='testrecord', constraint=models.CheckConstraint(condition=~models.Q(state='resolved') | ~models.Q(retest=''), name='resolved_requires_retest')),
    ]
