# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.utils
import manager.models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0007_bookmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='mei',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), upload_to=manager.models.Opus.upload_path, null=True),
        ),
    ]
