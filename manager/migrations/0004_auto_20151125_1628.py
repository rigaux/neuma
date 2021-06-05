# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.models
import manager.utils


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0003_remove_opus_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='lilypond',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), null=True, upload_to=manager.models.Opus.upload_path),
        ),
        migrations.AddField(
            model_name='opus',
            name='pdfile',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), null=True, upload_to=manager.models.Opus.upload_path),
        ),
        migrations.AddField(
            model_name='opus',
            name='pngfile',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), null=True, upload_to=manager.models.Opus.upload_path),
        ),
        migrations.AddField(
            model_name='opus',
            name='preview',
            field=models.FileField(storage=manager.utils.OverwriteStorage(), null=True, upload_to=manager.models.Opus.upload_path),
        ),
    ]
