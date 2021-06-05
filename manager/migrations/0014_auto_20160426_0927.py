# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.models
import manager.utils


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0013_auto_20160223_1534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opus',
            name='mei',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), null=True, max_length=255, upload_to=manager.models.Opus.upload_path),
        ),
    ]
