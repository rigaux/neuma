# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0009_opus_sequence'),
    ]

    operations = [
        migrations.RenameField(
            model_name='opus',
            old_name='sequence',
            new_name='music_summary',
        ),
    ]
