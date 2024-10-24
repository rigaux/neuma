# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-06-05 16:45
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transcription', '0002_grammar_parse_failures_ratio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grammar',
            name='parse_failures_ratio',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='grammarrule',
            name='body',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=40), size=None),
        ),
        migrations.AlterField(
            model_name='grammarstate',
            name='symbol',
            field=models.CharField(max_length=40, unique=True),
        ),
    ]
