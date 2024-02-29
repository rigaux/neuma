# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='QtDimension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('ref', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(null=True)),
            ],
            options={
                'db_table': 'QtDimension',
            },
        ),
        migrations.CreateModel(
            name='QtExpectedValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('expected_value', models.FloatField(null=True)),
            ],
            options={
                'db_table': 'QtExpectedValue',
            },
        ),
        migrations.CreateModel(
            name='QtMeasure',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('value', models.FloatField()),
                ('date', models.DateTimeField(verbose_name='Updated', auto_now=True)),
            ],
            options={
                'db_table': 'QtMeasure',
            },
        ),
        migrations.CreateModel(
            name='QtMetric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('ref', models.CharField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(null=True)),
                ('dimension', models.ForeignKey(null=True, to='quality.QtDimension',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'QtMetric',
            },
        ),
        migrations.CreateModel(
            name='QtProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('usage', models.CharField(max_length=80)),
                ('description', models.TextField(null=True)),
            ],
            options={
                'db_table': 'QtProfile',
            },
        ),
        migrations.AddField(
            model_name='qtmeasure',
            name='metric',
            field=models.ForeignKey(to='quality.QtMetric',on_delete=models.PROTECT),
        ),
        migrations.AddField(
            model_name='qtmeasure',
            name='opus',
            field=models.ForeignKey(to='manager.Opus',on_delete=models.PROTECT),
        ),
        migrations.AddField(
            model_name='qtexpectedvalue',
            name='metric',
            field=models.ForeignKey(to='quality.QtMetric',on_delete=models.PROTECT),
        ),
        migrations.AddField(
            model_name='qtexpectedvalue',
            name='profile',
            field=models.ForeignKey(to='quality.QtProfile',on_delete=models.PROTECT),
        ),
        migrations.AlterUniqueTogether(
            name='qtmeasure',
            unique_together=set([('opus', 'metric')]),
        ),
        migrations.AlterUniqueTogether(
            name='qtexpectedvalue',
            unique_together=set([('metric', 'profile')]),
        ),
    ]
