# Generated by Django 4.2 on 2025-01-02 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0105_alter_opussource_operations"),
    ]

    operations = [
        migrations.AddField(
            model_name="opussource",
            name="iiif_manifest",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
