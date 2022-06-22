# Generated by Django 3.1 on 2022-06-01 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0068_auto_20220601_1256'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='body',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='annot_body', to='manager.resource'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='target',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='annot_target', to='manager.resource'),
        ),
    ]