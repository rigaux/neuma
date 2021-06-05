# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('manager', '0006_opus_midi'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('timestamp', models.DateTimeField(verbose_name='Created', auto_now_add=True)),
                ('opus', models.ForeignKey(to='manager.Opus',on_delete=models.PROTECT)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'Bookmark',
            },
        ),
    ]
