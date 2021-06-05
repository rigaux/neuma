# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0004_auto_20151125_1628'),
    ]

    operations = [
        migrations.RenameField(
            model_name='opus',
            old_name='pdfile',
            new_name='pdf',
        ),
        migrations.RenameField(
            model_name='opus',
            old_name='pngfile',
            new_name='png',
        ),
    ]
