# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.models
import manager.utils


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0014_auto_20160426_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='summary',
            field=models.FileField(null=True, upload_to=manager.models.Opus.upload_path, storage=manager.utils.OverwriteStorage()),
        ),
    ]
