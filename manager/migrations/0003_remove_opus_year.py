# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0002_auto_20151125_1127'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opus',
            name='year',
        ),
    ]
