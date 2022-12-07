import logging
from lxml import etree

from django.contrib.postgres.fields import JSONField
from django.db import models

from columbine.models import ColumbineBaseModel
from columbine.soap import dict_to_root_xml, dict_to_xml

logger = logging.getLogger("django_columbine.%s" % __name__)


class Transaction(ColumbineBaseModel):
    """
    This models contains all Columbine API Transactions.
    A Flow often has more than one transaction, typically 1 or 3.
    """

    class Meta:
        # make sure each flow only has 1 transaction of each of validate/order/ack
        unique_together = [("flow", "stage")]

    flow = models.ForeignKey(
        "columbine.Flow",
        related_name="transactions",
        on_delete=models.PROTECT,
        help_text="The Flow to which this Transaction belongs",
    )

    TRANSACTION_STAGE_VALIDATE = "validate"
    TRANSACTION_STAGE_ORDER = "order"
    TRANSACTION_STAGE_ACKNOWLEDGE = "ack"
    TRANSACTION_STAGE_CHOICES = (
        (TRANSACTION_STAGE_VALIDATE, TRANSACTION_STAGE_VALIDATE),
        (TRANSACTION_STAGE_ORDER, TRANSACTION_STAGE_ORDER),
        (TRANSACTION_STAGE_ACKNOWLEDGE, TRANSACTION_STAGE_ACKNOWLEDGE),
    )

    stage = models.CharField(
        max_length=8,
        choices=TRANSACTION_STAGE_CHOICES,
        help_text="The stage of this transaction - validate, order or ack?",
    )

    request_json = JSONField(
        help_text="The request data for this Transaction (as JSON)"
    )

    request_xml_valid = models.NullBooleanField(
        help_text="True if the request XML is valid according to command.xsd, False if invalid, None if no validation has been attempted."
    )

    reply_json = JSONField(
        null=True, blank=True, help_text="The reply data for this Flow (as JSON)"
    )

    reply_xml_valid = models.NullBooleanField(
        help_text="True if the reply XML is valid according to reply.xsd, False if invalid, None if no validation has been attempted."
    )

    attempts = models.IntegerField(
        default=0,
        help_text="The number of times the request worker has attempted to process this transaction",
    )

    result = models.NullBooleanField(
        default=None,
        help_text="True if this transaction has been processed successfully by the columbine_flow_processor, False if an error happened while processing this Transaction, None if it hasn't been processed yet.",
    )

    error = JSONField(
        null=True,
        blank=True,
        help_text="Any error message from the <reply><error> element",
    )

    @property
    def request_xml(self):
        """
        Must return a string representing self.request_json as XML
        """
        return etree.tostring(dict_to_xml(self.request_json)[0]).decode("iso8859-1")

    @property
    def reply_xml(self):
        if self.reply_json:
            return etree.tostring(dict_to_xml(self.reply_json)[0]).decode("iso8859-1")

    @property
    def name(self):
        """
        The name of a transaction is the name of the flow, unless the
        stage is "validate" or "ack", in which case the transaction
        name is the flow name plus "-" plus the stage name.
        """
        if self.stage == self.TRANSACTION_STAGE_ORDER:
            return self.flow.name
        else:
            return self.flow.name + "-" + self.stage

    def get_columbine_envelope(self, transaction_name):
        """
        Return an XML element with Columbine system envelope
        """
        data = {
            "cb-system": {"session-id": self.flow.tag, "transaction-id": self.tag},
            "name": transaction_name,
        }
        if self.flow.columbine_session_id:
            # add columbine-session-id element to <cb-system>
            data["cb-system"]["columbine-session-id"] = self.flow.columbine_session_id

        # get and return the XML
        return dict_to_root_xml(name="command", data=data)
