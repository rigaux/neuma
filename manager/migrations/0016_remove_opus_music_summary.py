# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0015_opus_summary'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opus',
            name='music_summary',
        ),
    ]
