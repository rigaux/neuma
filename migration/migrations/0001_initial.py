# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0012_auto_20160203_1537'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorpusMigration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('tag', models.TextField()),
                ('creation_timestamp', models.DateTimeField(verbose_name='Created', auto_now_add=True)),
                ('update_timestamp', models.DateTimeField(verbose_name='Updated', auto_now=True)),
                ('corpus', models.OneToOneField(to='manager.Corpus',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'CorpusMigration',
            },
        ),
        migrations.CreateModel(
            name='OpusMigration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('tag', models.TextField()),
                ('creation_timestamp', models.DateTimeField(verbose_name='Created', auto_now_add=True)),
                ('update_timestamp', models.DateTimeField(verbose_name='Updated', auto_now=True)),
                ('opus', models.OneToOneField(to='manager.Opus',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'OpusMigration',
            },
        ),
    ]
