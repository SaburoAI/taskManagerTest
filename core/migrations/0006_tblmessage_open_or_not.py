# Generated by Django 5.1.4 on 2025-02-20 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_tblmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='tblmessage',
            name='open_or_not',
            field=models.BooleanField(default=False),
        ),
    ]
