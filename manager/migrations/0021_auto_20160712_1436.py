# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0020_auto_20160712_1349'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='kmeans',
            table='Kmeans',
        ),
    ]
