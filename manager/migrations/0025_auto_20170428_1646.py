# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-28 16:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0024_auto_20170428_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='analytic_concept',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.AnalyticConcept'),
        ),
    ]
