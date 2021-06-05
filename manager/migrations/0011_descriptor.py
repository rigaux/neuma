# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0010_auto_20160201_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='Descriptor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('part_id', models.IntegerField()),
                ('voice_id', models.IntegerField()),
                ('type', models.CharField(max_length=30)),
                ('value', models.TextField()),
                ('opus', models.ForeignKey(to='manager.Opus',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'Descriptor',
            },
        ),
    ]
