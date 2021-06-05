# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0012_auto_20160203_1537'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='corpus',
            options={'permissions': (('view_corpus', 'View corpus'),)},
        ),
    ]
