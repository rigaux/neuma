# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.models
import manager.utils


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0005_auto_20151125_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='midi',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), null=True, upload_to=manager.models.Opus.upload_path),
        ),
    ]
