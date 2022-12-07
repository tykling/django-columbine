import logging

from django.db import transaction

from columbine.models import Order

logger = logging.getLogger("django_columbine.%s" % __name__)


def do_work():
    """
    This worker takes care of creating new Columbine Flows as needed:
    - It creates new OrderFlows if any Order objects need it
    - TODO: Create GetEventStatus flows hourly to see if we need to get any events.
    """
    # we manage the transaction manually, otherwise the first order.save()
    # will release the lock, which is not (always) what we want.
    with transaction.atomic():
        order = (
            Order.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(
                # Find all Orders which do not have a Flow yet
                flow__isnull=True
            )
            .first()
        )

        if not order:
            # No Orders to handle right now
            return

        logger.debug("Calling order.create_order_flow() for %s" % order)
        order.create_order_flow()
