# Generated by Django 2.2.6 on 2019-10-24 09:27

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("columbine", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="flow",
            name="references",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                help_text="References for this Flow"
            ),
        )
    ]
