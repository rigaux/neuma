# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.models
import manager.utils


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0016_remove_opus_music_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='lilypreview',
            field=models.FileField(upload_to=manager.models.Opus.upload_path, null=True, storage=manager.utils.OverwriteStorage()),
        ),
    ]
