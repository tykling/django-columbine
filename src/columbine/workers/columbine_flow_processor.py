import logging

from django.db import transaction

from columbine.models import Flow

logger = logging.getLogger("django_columbine.%s" % __name__)


def do_work():
    """
    This worker takes care of processing Columbine Flows.
    """
    # we manage the transaction manually, otherwise the first tx.save()
    # will release the lock, which is not (always) what we want.
    with transaction.atomic():
        flow = (
            Flow.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(
                # Pick all Flows that are unfinished
                finished=False,
                # and where we have an unprocessed transaction
                transactions__result__isnull=True,
                # where the HTTP request has been made
                transactions__request__isnull=False,
            )
            .first()
        )

        if not flow:
            # No Flows to handle right now
            return

        logger.debug("Processing %s" % flow.tag)
        flow.process()
        logger.debug("Done processing %s" % flow.tag)
