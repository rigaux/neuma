# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0008_opus_mei'),
    ]

    operations = [
        migrations.AddField(
            model_name='opus',
            name='sequence',
            field=models.TextField(null=True),
        ),
    ]
