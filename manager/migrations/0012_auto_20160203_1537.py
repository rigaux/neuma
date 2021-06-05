# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0011_descriptor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='descriptor',
            name='part_id',
        ),
        migrations.RemoveField(
            model_name='descriptor',
            name='voice_id',
        ),
        migrations.AddField(
            model_name='descriptor',
            name='part',
            field=models.CharField(max_length=30, default='kj'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='descriptor',
            name='voice',
            field=models.CharField(max_length=30, default='vv'),
            preserve_default=False,
        ),
    ]
