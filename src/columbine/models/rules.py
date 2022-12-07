import logging

from django.db import models

from columbine.models import ColumbineBaseModel

logger = logging.getLogger("django_columbine.%s" % __name__)


class ProductCountRule(ColumbineBaseModel):
    """
    The ProductCountRule model contains the rules for how many products
    we can minimum and maximum order of a given product.
    """

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="productcountrules",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        help_text="The OrderFlow in which this ProductCountRule was first seen.",
    )

    product = models.ForeignKey(
        "columbine.Product",
        related_name="product_count_rules",
        on_delete=models.PROTECT,
        help_text="The Columbine Product which this product count rule relates to",
    )

    min_value = models.IntegerField(
        help_text="The minimum number of times this product can be ordered"
    )

    max_value = models.IntegerField(
        help_text="The maximum number of times this product can be ordered"
    )


class ProductGroupCountRule(ColumbineBaseModel):
    """
    The ProductGroupCountRule model contains all the rules which define
    how many Products in a ProductGroup we may order.
    TODO: Implement the logic to actually use these rules once TDC gets them fixed,
    at the moment it is impossible for us to match the rules to the productgroups,
    since the rules include no name for the productgroup.
    """

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="productgroupcountrules",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        help_text="The OrderFlow in which this RelationRuleType was first seen.",
    )

    productgroup = models.ForeignKey(
        "columbine.ProductGroup",
        related_name="productgroupcountrules",
        on_delete=models.PROTECT,
        help_text="The Columbine Productgroup which this productgroup count rule comes from",
    )

    min_value = models.IntegerField(
        help_text="The minimum number of times this productgroup can be ordered"
    )

    max_value = models.IntegerField(
        help_text="The maximum number of times this productgroup can be ordered"
    )


class RelationRuleType(ColumbineBaseModel):
    """
    This model contains the different Columbine rule types.
    We get_or_create when we see a rule and leave the data in the table.
    """

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="relationruletypes",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        help_text="The OrderFlow in which this RelationRuleType was first seen.",
    )

    name = models.CharField(
        max_length=100, unique=True, help_text="The name of this RelationRuleType"
    )

    descr = models.TextField(
        help_text="Columbines description of this RelationRuleType"
    )


class RelationRule(ColumbineBaseModel):
    """
    The RelationRule model contains all the rules that govern the relations between products.
    It has three m2ms to the Product table, and an FK to RelationRuleType which shows the type of rule.
    """

    ruletype = models.ForeignKey(
        "columbine.RelationRuleType",
        related_name="relationrules",
        on_delete=models.PROTECT,
        help_text="The type of this RelationRule",
    )

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="relationrules",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        help_text="The OrderFlow to which this RelationRule belongs.",
    )

    rule_group_1_products = models.ManyToManyField(
        "columbine.Product",
        related_name="rule_group_1_rules",
        help_text="The products in rule group 1 for this rule",
    )

    rule_group_2_products = models.ManyToManyField(
        "columbine.Product",
        related_name="rule_group_2_rules",
        help_text="The products in rule group 2 for this rule (if any)",
    )

    rule_group_3_products = models.ManyToManyField(
        "columbine.Product",
        related_name="rule_group_3_rules",
        help_text="The products in rule group 3 for this rule (if any)",
    )
