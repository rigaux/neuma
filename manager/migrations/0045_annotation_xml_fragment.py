# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-09-04 14:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0044_auto_20180605_1713'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='xml_fragment',
            field=models.TextField(default='', null=True),
        ),
    ]
