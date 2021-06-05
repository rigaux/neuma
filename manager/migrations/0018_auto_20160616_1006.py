# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import manager.utils
import manager.models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0017_opus_lilypreview'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimMatrix',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('ref', models.CharField(unique=True, max_length=255)),
                ('value', models.FloatField()),
                ('opus1', models.ForeignKey(related_name='manager_simmatrix_opus1', to='manager.Opus',on_delete=models.PROTECT)),
                ('opus2', models.ForeignKey(related_name='manager_simmatrix_opus2', to='manager.Opus',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'SimMatrix',
            },
        ),
        migrations.CreateModel(
            name='SimMeasure',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('code', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'db_table': 'SimMeasure',
            },
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('description', models.TextField()),
                ('creation_timestamp', models.DateTimeField(verbose_name='Created', auto_now_add=True)),
                ('update_timestamp', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('zip_file', models.FileField(null=True, upload_to=manager.models.Upload.upload_path, storage=manager.utils.OverwriteStorage())),
                ('corpus', models.OneToOneField(to='manager.Corpus',on_delete=models.PROTECT)),
            ],
            options={
                'db_table': 'Upload',
            },
        ),
        migrations.AddField(
            model_name='simmatrix',
            name='sim_measure',
            field=models.ForeignKey(to='manager.SimMeasure',on_delete=models.PROTECT),
        ),
    ]
