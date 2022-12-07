# Generated by Django 2.2.6 on 2019-11-07 08:39

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("columbine", "0006_auto_20191106_1436")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="reason",
            field=models.TextField(
                default="",
                help_text="The reason we created this Order, as a text string",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="source",
            field=models.TextField(
                default="",
                help_text="The module.class.method() and lineno where we created this Order",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="order",
            name="references",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                help_text="Any external reference data for this Order"
            ),
        ),
    ]