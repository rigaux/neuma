# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0019_remove_simmatrix_ref'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kmeans',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('tag', models.CharField(max_length=255, unique=True)),
                ('group', models.IntegerField()),
                ('corpus', models.ForeignKey(to='manager.Corpus',on_delete=models.PROTECT)),
            ],
        ),
        migrations.AlterField(
            model_name='upload',
            name='corpus',
            field=models.ForeignKey(to='manager.Corpus',on_delete=models.PROTECT),
        ),
    ]
