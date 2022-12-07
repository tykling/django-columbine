import logging

from django.db import models
from django.contrib.postgres.fields import JSONField

from columbine.models import ColumbineBaseModel

logger = logging.getLogger("django_columbine.%s" % __name__)


class ProductGroup(ColumbineBaseModel):
    """
    A ProductGroup can contain 1-many Products, and the same Product can be in 0-many groups.
    A ProductGroup is identified by a combination of product_group_id, product_group_name and
    sik_value. TODO: The ProductGroupCountRules we get with each order does not include the
    product_group_name so we cannot identify which ProductGroup goes with which rule :(
    """

    class Meta:
        unique_together = [("product_group_id", "product_group_name", "sik_value")]

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="productgroups",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        help_text="The OrderFlow in which this ProductGroup was first seen.",
    )

    product_group_id = models.TextField(
        help_text="The Columbine id for this productgroup"
    )

    product_group_name = models.TextField(
        help_text="The Columbine name for this productgroup"
    )

    sik_value = models.TextField(
        help_text="The Columbine sik value for the productgroup"
    )

    products = models.ManyToManyField(
        "columbine.Product", help_text="The products included in this productgroup"
    )


class Product(ColumbineBaseModel):
    class Meta:
        unique_together = [("product_id", "sik_value")]

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="products",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        help_text="The OrderFlow in which this Product was first seen.",
    )

    product_id = models.TextField(help_text="The Columbine product-id for the product.")

    name = models.TextField(
        null=True, blank=True, help_text="The Columbine product name for this product"
    )

    descr = models.TextField(
        null=True,
        blank=True,
        help_text="The Columbine product description (often missing)",
    )

    sik_value = models.TextField(help_text="The Columbine sik value for the product")

    product_parameter_type_list = JSONField(
        null=True,
        blank=True,
        help_text="The XML describing any parameters for this product (as JSON)",
    )
