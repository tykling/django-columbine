import logging

from django.db import transaction

from columbine.models import Flow, Transaction
import columbine.flows

logger = logging.getLogger("django_columbine.%s" % __name__)


def do_work():
    """
    The columbine_transaction_creator worker creates new
    Transaction objects based on unfinished Flow objects.
    """
    # we manage the transaction manually, otherwise the first
    # flow.save() will release the lock, which is not always what we want
    with transaction.atomic():
        # Get the oldest flow, use select_for_update(skip_locked=True)
        # so multiple workers can run simultaneously without accidently
        # picking the same Flow to work on.
        flow = (
            Flow.objects.select_for_update(
                # skip any Flows that are locked by some other worker
                skip_locked=True,
                # only lock the Flow itself, not the related objects
                of=("self",),
            )
            .filter(
                # we only want flows that are not already finished
                finished=False
            )
            .exclude(
                # Exclude flows which have unprocessed transactions,
                # we don't want to create a new TX before the previous has
                # been processed!
                transactions__isnull=False,
                transactions__result__isnull=True,
            )
            .first()
        )

        # do we have a flow?
        if not flow:
            return

        logger.debug("Picked %s" % flow)

        # import flowclass
        try:
            flowclass = getattr(columbine.flows, flow.name)()
            logger.debug("imported flowclass %s" % flow.name)
        except ValueError:
            logger.error("Unable to import flowclass for %s" % flow.name)
            return

        # do we need a VALIDATE transaction for this type of flow?
        if flowclass.require_validate and not flow.get_validate_tx:
            # create the VALIDATE Transaction and return
            flow.create_transaction(stage=Transaction.TRANSACTION_STAGE_VALIDATE)
            return

        # this flow has been validated, or does not require validation,
        # do we need to create an ORDER transaction?
        if not flow.get_order_tx:
            flow.create_transaction(stage=Transaction.TRANSACTION_STAGE_ORDER)
            return

        # do we need an ACK transaction for this type of flow?
        if flowclass.require_acknowledge and not flow.get_acknowledge_tx:
            # create the VALIDATE Transaction and return
            flow.create_transaction(stage=Transaction.TRANSACTION_STAGE_ACKNOWLEDGE)
            return
