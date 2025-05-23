# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-12 16:00
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('manager', '0041_annotation_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grammar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('ns', models.CharField(max_length=20, unique=True)),
                ('meter_nb_beats', models.IntegerField()),
                ('meter_beat_unit', models.IntegerField()),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('update_timestamp', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('corpus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Corpus')),
            ],
            options={
                'db_table': 'Grammar',
            },
        ),
        migrations.CreateModel(
            name='GrammarRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField(default=0.0)),
                ('body', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=10), size=None)),
                ('grammar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transcription.Grammar')),
            ],
            options={
                'db_table': 'GrammarRule',
            },
        ),
        migrations.CreateModel(
            name='GrammarState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=20, unique=True)),
                ('type', models.CharField(default='NT', max_length=2)),
                ('nb_grace_notes', models.IntegerField(default=0)),
                ('grammar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transcription.Grammar')),
            ],
            options={
                'db_table': 'GrammarState',
            },
        ),
        migrations.AddField(
            model_name='grammarrule',
            name='head',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transcription.GrammarState'),
        ),
    ]
