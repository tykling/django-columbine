# Generated by Django 2.2.6 on 2019-11-06 13:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("columbine", "0005_auto_20191106_1426")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="flow",
            field=models.ForeignKey(
                help_text="The OrderFlow in which this Product was first seen.",
                limit_choices_to={"name__endswith": "OrderFlow"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="columbine.Flow",
            ),
        ),
        migrations.AlterField(
            model_name="productcountrule",
            name="flow",
            field=models.ForeignKey(
                help_text="The OrderFlow in which this ProductCountRule was first seen.",
                limit_choices_to={"name__endswith": "OrderFlow"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productcountrules",
                to="columbine.Flow",
            ),
        ),
        migrations.AlterField(
            model_name="productgroup",
            name="flow",
            field=models.ForeignKey(
                help_text="The OrderFlow in which this ProductGroup was first seen.",
                limit_choices_to={"name__endswith": "OrderFlow"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productgroups",
                to="columbine.Flow",
            ),
        ),
        migrations.AlterField(
            model_name="productgroupcountrule",
            name="flow",
            field=models.ForeignKey(
                help_text="The OrderFlow in which this RelationRuleType was first seen.",
                limit_choices_to={"name__endswith": "OrderFlow"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productgroupcountrules",
                to="columbine.Flow",
            ),
        ),
        migrations.AlterField(
            model_name="relationrule",
            name="flow",
            field=models.ForeignKey(
                help_text="The OrderFlow to which this RelationRule belongs.",
                limit_choices_to={"name__endswith": "OrderFlow"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="relationrules",
                to="columbine.Flow",
            ),
        ),
        migrations.AlterField(
            model_name="relationruletype",
            name="flow",
            field=models.ForeignKey(
                help_text="The OrderFlow in which this RelationRuleType was first seen.",
                limit_choices_to={"name__endswith": "OrderFlow"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="relationruletypes",
                to="columbine.Flow",
            ),
        ),
    ]
