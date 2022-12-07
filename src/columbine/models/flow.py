import inspect
import logging
import xmltodict
from lxml import etree

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

import columbine.flows
from columbine.models import ColumbineBaseModel
from columbine.xsd import validate_command_xml

logger = logging.getLogger("django_columbine.%s" % __name__)


class Flow(ColumbineBaseModel):
    """
    This model contains all Columbine API Flows.
    A Flow consists of 1 to 3 transactions.
    Flows are created in external code, and sometimes internally in
    django-columbine in the reply_handler of another Flow.
    """

    name = models.CharField(
        max_length=100,
        # make sure we always use Flow names from columbine.flows,
        # this means a new migration whenever we add/remove classes there
        choices=[
            (flowname, flowname)
            for flowname, flowclass in inspect.getmembers(
                columbine.flows, inspect.isclass
            )
        ],
        help_text="The Type of this Flow (must be a class from columbine.flows)",
    )

    kwargs = JSONField(default=dict, help_text="The data for this Flow (as JSON)")

    reason = models.TextField(
        help_text="The reason we created this Flow, as a text string"
    )

    source = models.TextField(
        help_text="The module.class.method() where we created this Flow"
    )

    references = JSONField(help_text="References for this Flow")

    parent_flow = models.ForeignKey(
        "columbine.Flow",
        related_name="child_flows",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text="The parent Flow of this Flow",
    )

    columbine_session_id = models.CharField(
        max_length=50, help_text="The Columbine generated session ID", blank=True
    )

    finished = models.BooleanField(
        default=False,
        help_text="True if this Flow is considered finished (by our end). A finished flow will not be touched again by the workers.",
    )

    result = models.NullBooleanField(
        help_text="True if all Transactions for this Flow have been make and their responses processed successfully in our end, False if an error happened during reply handling, None as long as we haven't fully processed the Flow yet."
    )

    error = JSONField(null=True, blank=True, help_text="Any errormessage for this flow")

    def clean(self):
        """
        Try to import and instantiate the flowclass
        """
        try:
            getattr(columbine.flows, self.name)()
        except ValueError:
            raise ValidationError(
                "Class name %s must be a valid class in columbine.flows" % self.name
            )

    @property
    def attempts(self):
        """
        Return the Sum() of all transaction attempts
        """
        return self.transactions.aggregate(models.Sum("attempts"))["attempts__sum"]

    @property
    def is_finished(self):
        """
        Return True if all transactions needed by this flow exists
        and are processed, False otherwise.
        """
        # import the flowclass
        flowclass = getattr(columbine.flows, self.name)()

        # if we need a VALIDATE tx and don't have one, return False
        if flowclass.require_validate and not self.get_validate_tx:
            return False

        # if we don't have an ORDER tx return False
        if not self.get_order_tx:
            return False

        # if we need an ACKNOWLEDGE tx and don't have one, return False
        if flowclass.require_acknowledge and not self.get_acknowledge_tx:
            return False

        # if any transactions are not processed return False
        if self.transactions.filter(result__isnull=True).exists():
            return False

        # looks like we're good, take him away boys
        return True

    @property
    def get_validate_tx(self):
        """
        Return True if this Flow has a VALIDATE transaction,
        False otherwise
        """
        from columbine.models import Transaction

        try:
            return self.transactions.get(stage=Transaction.TRANSACTION_STAGE_VALIDATE)
        except Transaction.DoesNotExist:
            return False

    @property
    def validate_result(self):
        """
        Return True if this flow has a successful TRANSACTION_STAGE_VALIDATE Transaction,
        False if it has an unsuccessful, and None if it has no VALIDATE Transaction.
        """
        tx = self.get_validate_tx()
        if tx:
            return tx.success

    @property
    def get_order_tx(self):
        """
        Return True if this Flow has an Order transaction,
        False otherwise
        """
        from columbine.models import Transaction

        try:
            return self.transactions.get(stage=Transaction.TRANSACTION_STAGE_ORDER)
        except Transaction.DoesNotExist:
            return False

    @property
    def get_acknowledge_tx(self):
        """
        Return True if this Flow has a ACKNOWLEDGE transaction,
        False otherwise
        """
        from columbine.models import Transaction

        try:
            return self.transactions.get(
                stage=Transaction.TRANSACTION_STAGE_ACKNOWLEDGE
            )
        except Transaction.DoesNotExist:
            return False

    @property
    def acknowledge_result(self):
        """
        Return True if this flow has a successful
        TRANSACTION_STAGE_ACKNOWLEDGE Transaction,
        False if it has an unsuccessful, and None
        if it has no ACKNOWLEDGE Transaction.
        """
        tx = self.get_acknowledge_tx()
        if tx:
            return tx.success

    def create_transaction(self, stage):
        """
        Create a new transaction belonging to this flow.

        Args:
            stage (str): One of Transaction.TRANSACTION_STAGE_CHOICES

        Returns:
            An Instance of columbine.models.Transaction
        """
        logger.debug("Creating a new %s transaction for flow %s" % (stage, self))

        # import the flow class
        try:
            flowclass = getattr(columbine.flows, self.name)()
        except ValueError:
            logger.error(
                "Unable to import flowclass named %s - it must be a valid class in columbine.flows"
                % self.name
            )
            return False

        # create the Transaction
        from columbine.models import Transaction

        tx = Transaction(flow=self, stage=stage)

        # get columbine system XML envelope
        txname = flowclass.get_tx_name(stage)
        xmlroot = tx.get_columbine_envelope(transaction_name=txname)

        # get xml body
        body = flowclass.get_xml_body(tx)
        if body is None:
            logger.error("We got no XML body from flowclass %s" % flowclass)
            return False
        # add xml body
        xmlroot.append(body)

        # validate the XML
        validxml = validate_command_xml(xmlroot)

        # get a string of the xml object and convert to a dict
        xml = etree.tostring(xmlroot, encoding="utf-8").decode("utf-8")
        xmldict = xmltodict.parse(xml, dict_constructor=dict)

        # save XML to transaction
        tx.request_json = xmldict
        tx.request_xml_valid = validxml
        tx.save()
        logger.info("Created new %s Transaction %s for flow %s" % (stage, tx, self))

        # all good
        return tx

    def success(self):
        """
        A flow is considered a success if all transactions have been processed and were successful
        """
        if not self.is_finished:
            # flow not finished, success status unknown
            return None

        if self.transactions.filter(success=False).exists():
            # one or more transactions was not successful
            return False

        # all good
        return True

    def process(self):
        """
        The Flow.process method is called by the columbine_flow_processor
        It can be called multiple times per flow.
        This implements the overall logic surrounding flow handling.
        """
        # is this flow already marked as finished?
        if self.finished:
            logger.info("%s is finished, nothing to do" % self.tag)
            return

        # should this flow have been marked as finished?
        if self.is_finished:
            logger.info("%s is finished, marking as finished" % self.tag)
            self.finished = True
            self.save()
            return

        logger.info("Processing %s" % self.tag)

        # import flowclass
        try:
            flowclass = getattr(columbine.flows, self.name)()
            print("imported flowclass %s" % self.name)
        except ValueError:
            logger.error("Unable to import flowclass for %s" % self)
            return False

        # Find the first unprocessed transaction (result__isnull=True)
        # where the HTTP request has been made (request__isnull=False)
        # by the columbine_request_worker already. This TX can be any
        # stage - VALIDATE, ORDER, or ACK.
        tx = self.transactions.filter(
            result__isnull=True, request__isnull=False
        ).first()
        if not tx:
            logger.error("Nothing to do for %s" % self)
            return
        logger.info("Processing %s" % tx.tag)

        if tx.error:
            # this TX resulted in an XML error, no need to handle_reply
            logger.debug("%s has error, no need to handle_reply()" % tx)
            tx.result = False
            self.error = tx.error
        else:
            # This TX needs reply handling, the flowclass knows how to
            # handle the reply, it will return True/False
            tx.result = flowclass.handle_reply(tx)
        logger.debug("Saving Transaction, tx.result is %s" % tx.result)

        # save transaction
        tx.save()

        # is this flow finished now, did all transactions succeed?
        if flowclass.require_validate:
            if self.get_validate_tx is False:
                if not self.get_validate_tx.result:
                    # VALIDATE TX failed, mark Flow as finished and fail
                    self.finished = True
                    self.result = False
                    self.save()
                    return

        if self.get_order_tx:
            if self.get_order_tx.result is False:
                # ORDER TX failed, mark Flow as finished and fail
                self.finished = True
                self.result = False
                self.save()
                return

        if flowclass.require_acknowledge:
            if self.get_acknowledge_tx:
                if self.get_acknowledge_tx.result is False:
                    # ACKNOWLEDGE TX failed, mark Flow finished and fail
                    self.finished = True
                    self.result = False
                    self.save()
                    return

        # If we got this far no transactions failed.
        # Do we have all required Transactions for this Flow?
        if self.transactions.count() == flowclass.transaction_count:
            # this Flow is finished, and was successful!
            self.finished = True
            self.result = True

        # all done
        self.save()
        logger.debug("Leaving Flow.process() for %s" % self.tag)
