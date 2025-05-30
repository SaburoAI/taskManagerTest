# Generated by Django 5.1.4 on 2025-02-20 06:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_tblschoolid_s_name_tbluser_user_simei_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TblMessage',
            fields=[
                ('id', models.SmallAutoField(primary_key=True, serialize=False)),
                ('message', models.TextField()),
                ('read', models.BooleanField(default=False)),
                ('update_date', models.DateTimeField(auto_now=True, null=True)),
                ('reg_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='core.tbluser')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='core.tbluser')),
            ],
            options={
                'db_table': 'tbl_message',
                'managed': True,
            },
        ),
    ]
