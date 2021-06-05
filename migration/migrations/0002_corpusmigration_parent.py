# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('migration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpusmigration',
            name='parent',
            field=models.ForeignKey(to='migration.CorpusMigration', null=True,on_delete=models.PROTECT),
        ),
    ]
