# Generated by Django 3.1 on 2022-10-21 15:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0081_auto_20221019_1439'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opus',
            name='dmos_json',
        ),
        migrations.RemoveField(
            model_name='opus',
            name='midi',
        ),
        migrations.RemoveField(
            model_name='opus',
            name='pdf',
        ),
        migrations.RemoveField(
            model_name='opus',
            name='png',
        ),
        migrations.RemoveField(
            model_name='opus',
            name='preview',
        ),
        migrations.RemoveField(
            model_name='opus',
            name='record',
        ),
    ]
