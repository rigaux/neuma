# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.utils
import manager.models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='musicxml',
            field=models.FileField(upload_to=manager.models.Opus.upload_path, null=True, storage=manager.utils.OverwriteStorage()),
        ),
        migrations.AlterField(
            model_name='corpus',
            name='cover',
            field=models.FileField(upload_to=manager.models.Corpus.upload_path, null=True, storage=manager.utils.OverwriteStorage()),
        ),
        migrations.AlterField(
            model_name='opus',
            name='ref',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
