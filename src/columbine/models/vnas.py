import logging
from typing import Optional

from django.contrib.postgres.fields import JSONField
from django.db import models

from columbine.models import ColumbineBaseModel

logger = logging.getLogger("django_columbine.%s" % __name__)


class VNAS(ColumbineBaseModel):
    """
    This model contains TDC circuit data returned by the
    ShowNetInfoVNASFlow. We create an instance of this
    model every time we get a ShowNetInfoVNASFlow reply.
    Old entries can be deleted after a while since new
    measurements make them worthless to keep.
    """

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="vnass",
        on_delete=models.PROTECT,
        limit_choices_to={
            "name": "ShowNetInfoVNASFlow",
            "finished": True,
            "result": True,
        },
        help_text="The ShowNetInfoVNASFlow from which this VNAS came",
    )

    references = JSONField(
        null=True,
        blank=True,
        help_text="Any external reference data for this VNAS, copied from the ShowNetInfoVNASFlow it came from",
    )

    data = JSONField(help_text="The data for this VNAS")

    @property
    def order_flow_type(self) -> Optional[str]:
        """
        Return the name of the flow used to order the type of technology this VNAS uses
        """
        if self.data["equipType"] == "COPPER":
            return "VULAOrderFlow"
        elif self.data["equipType"] == "FIBER ENABLED":
            return "FBSAOrderFlow"
        elif self.data["equipType"] == "COAX":
            return "COAXOrderFlow"
        else:
            logger.error("Unknown technology!")
            return None

    @property
    def order_client_method(self) -> Optional[str]:
        """
        Return the name of the method to call to order type of technology this VNAS uses,
        or None if the equpment type is unknown
        """
        if self.data["equipType"] == "COPPER":
            return "vula"
        elif self.data["equipType"] == "FIBER ENABLED":
            return "fbsa"
        elif self.data["equipType"] == "COAX":
            return "coax"
        else:
            logger.error("Unknown technology!")
            return None
