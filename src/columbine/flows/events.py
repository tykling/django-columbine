import logging
import inspect

from columbine.soap import rename_dict_keys
from .base import ColumbineBaseFlow

logger = logging.getLogger("django_columbine.%s" % __name__)


class GetEventsFlow(ColumbineBaseFlow):
    """
    GetEventsFlow is used to get events from our "mailbox" at TDC.
    This flow is unusual because it has no Validate TX, but it has
    an Acknowledge TX.
    """

    name = "get-events"
    servicename = "getEvents"
    reply_element_name = "event-list"
    require_acknowledge = True

    def get_xml_body(self, tx):
        """
        The ACKNOWLEDGE tx needs the event-list-batch-no from the
        ORDER tx appended to parameter-list
        """
        # get basic <parameter-list> with <maximum-elements-returned>
        root = super().get_xml_body(tx)

        # if this is an ACK TX add <event-list-batch-no> from ORDER reply
        if tx.stage == "ack":
            # we need to include the event batch ID in the ACK
            # parse the XML from the ORDER tx
            batchno = tx.flow.get_order_tx.reply_json["reply"]["parameter_list"][
                "event_list_batch_no"
            ]
            root.append(self.element("event-list-batch-no", batchno))
        return root

    def handle_reply(self, tx):
        """
        Save events from the ORDER tx
        """
        # if this is stage ACK just return
        if tx.stage == "ack":
            return True

        # loop over events in the event-list and save each to DB
        for name, events in tx.reply_json["reply"]["event_list"].items():
            # only one item? wrap it in a list
            if isinstance(events, dict):
                events = [events]

            # loop over events of this type
            for event in events:
                from columbine.models import Event

                dbevent = Event.objects.create(
                    transaction=tx, name=name, jsonbody=rename_dict_keys(event)
                )

                logger.debug("Created new Event object %s" % dbevent)

        # we're done here
        return True


class GetEventStatusFlow(ColumbineBaseFlow):
    """
    The GetEventStatusFlow is used to check how many events we have
    waiting in our "mailbox" at TDC
    """

    name = "get-event-status"
    servicename = "getEventStatus"
    reply_element_name = "event-status"

    def handle_reply(self, tx):
        # do we have any unread events?
        unread = tx.reply_json["reply"]["event_status"]["unread_events"]
        if unread:
            message = (
                "get-event-status says we have %s events waiting in Columbine, creating a new GetEvents flow..."
                % unread
            )
            logger.info(message)
            from columbine.clients import GetEventsClient

            newflow = GetEventsClient(
                reason=message,
                source=self.get_source(
                    line=inspect.getframeinfo(inspect.currentframe()).lineno
                ),
                parent_flow=tx.flow,
            ).get_events()
            logger.info("created GetEvents flow %s" % newflow)

        # all good
        return True
