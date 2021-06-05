# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Corpus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('short_title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('short_description', models.TextField()),
                ('is_public', models.BooleanField(default=True)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('update_timestamp', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('ref', models.CharField(unique=True, max_length=255)),
                ('cover', models.FileField(upload_to='corpora', null=True)),
                ('parent', models.ForeignKey(to='manager.Corpus', null=True,on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'Corpus',
            },
        ),
        migrations.CreateModel(
            name='Opus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('year', models.IntegerField()),
                ('lyricist', models.CharField(max_length=255)),
                ('composer', models.CharField(max_length=255)),
                ('ref', models.CharField(max_length=255)),
                ('corpus', models.ForeignKey(to='manager.Corpus',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'Opus',
            },
        ),
    ]
