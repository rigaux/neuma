# Generated by Django 3.1 on 2022-10-21 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0084_auto_20221021_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opussource',
            name='url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
