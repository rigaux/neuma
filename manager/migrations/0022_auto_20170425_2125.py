# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-25 21:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0021_auto_20160712_1436'),
    ]

    operations = [
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analytic_concept', models.CharField(max_length=30)),
                ('fragment', models.TextField()),
                ('opus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Opus')),
            ],
            options={
                'db_table': 'Annotation',
            },
        ),
        migrations.AddField(
            model_name='kmeans',
            name='measure',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='manager.SimMeasure'),
            preserve_default=False,
        ),
    ]
