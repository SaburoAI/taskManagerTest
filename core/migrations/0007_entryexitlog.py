# Generated by Django 5.1.4 on 2025-04-08 10:55

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_tblmessage_open_or_not'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntryExitLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='入室時間')),
                ('exit_time', models.DateTimeField(blank=True, null=True, verbose_name='退室時間')),
                ('duration', models.DurationField(blank=True, null=True, verbose_name='滞在時間')),
                ('status', models.CharField(choices=[('entered', '入室中'), ('exited', '退室済み')], default='entered', max_length=10, verbose_name='状態')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entry_exit_logs', to='core.tbluser')),
            ],
        ),
    ]
