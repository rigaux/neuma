# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-11 20:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0031_auto_20170510_1149'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='corpus',
            options={'permissions': (('view_corpus', 'View corpus'), ('import_corpus', 'Import corpus'))},
        ),
    ]
