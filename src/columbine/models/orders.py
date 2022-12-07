import logging
import inspect

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

from columbine.models import ColumbineBaseModel
from columbine.clients import OrderClient
from columbine.soap import rename_dict_keys

logger = logging.getLogger("django_columbine.%s" % __name__)


class Order(ColumbineBaseModel):
    """
    The Order model contains all the orders we send to Columbine.
    An Order is linked to a VNAS so we know which tdc circuit to use.
    """

    vnas = models.ForeignKey(
        "columbine.VNAS",
        related_name="orders",
        on_delete=models.PROTECT,
        help_text="The Columbine VNAS this Order is based on",
    )

    products = models.ManyToManyField(
        "columbine.Product",
        through="columbine.OrderLine",
        related_name="orders",
        help_text="The Products included in this Order",
    )

    available_products = models.ManyToManyField(
        "columbine.Product",
        related_name=None,
        help_text="The Products available to this Order",
    )

    references = JSONField(help_text="Any external reference data for this Order")

    reason = models.TextField(
        help_text="The reason we created this Order, as a text string"
    )

    source = models.TextField(
        help_text="The module.class.method() and lineno where we created this Order"
    )

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="orders",
        on_delete=models.PROTECT,
        limit_choices_to={"name__endswith": "OrderFlow"},
        null=True,
        blank=True,
        help_text="The OrderFlow created to handle this Order.",
    )

    def create_order_flow(self) -> None:
        """
        This method is called by the columbine flow creator worker
        whenever it encounters a new Order object without a Flow object.
        """

        # get client object
        client = OrderClient(
            reason=f"Creating new {self.vnas.order_flow_type} for {self.tag}",
            source=f"{self.__module__}.{self.__class__.__name__}.{inspect.stack()[0][3]}() line {inspect.getframeinfo(inspect.currentframe()).lineno}",
            references=self.references,
        )

        # get address kwargs from the flow which order.vnas was retrieved with
        kwargs = self.vnas.flow.kwargs
        # remove VNAS from kwargs,
        # TODO: then how the hell do we ask for a specific columbine circuit/vnas?
        del kwargs["visitationNodeAnalysisSeq"]
        # convert dashes to underscores
        kwargs = rename_dict_keys(kwargs)

        # get the method and call the flow
        flow = getattr(client, self.vnas.order_client_method)(**kwargs)
        logger.info("Created flow %s" % flow)
        self.flow = flow
        self.save()


class OrderLine(ColumbineBaseModel):
    """
    The "through" model used to keep metadata about the Product on the Order
    """

    order = models.ForeignKey(
        "columbine.Order",
        related_name="orderlines",
        on_delete=models.PROTECT,
        help_text="The Columbine Order",
    )

    product = models.ForeignKey(
        "columbine.Product",
        related_name="orderlines",
        on_delete=models.PROTECT,
        help_text="The Columbine Product",
    )

    count = models.IntegerField(
        default=1, help_text="How many of this product do we want in the Order"
    )

    product_parameter_type_list = JSONField(
        null=True, blank=True, help_text="The product parameters (if any), as JSON"
    )

    def clean(self) -> None:
        if self.order.flow != self.product.transaction.flow:
            raise ValidationError("Something is fucky")
