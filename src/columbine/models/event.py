import logging
from datetime import datetime

from django.db import models
from django.contrib.postgres.fields import JSONField

from columbine.models import ColumbineBaseModel

logger = logging.getLogger("django_columbine.%s" % __name__)


class Event(ColumbineBaseModel):
    """
    This class contains all the events from the Columbine
    Event system (or "mailbox" as the docs refer to it)
    """

    transaction = models.ForeignKey(
        "columbine.Transaction",
        on_delete=models.PROTECT,
        help_text="The Transaction this event was received in",
    )

    jsonbody = JSONField(help_text="The body of this event (as JSON)")

    name = models.CharField(max_length=255, help_text="Event name")

    @property
    def event_id(self):
        return self.jsonbody.get("event_id")

    @property
    def phone_number(self):
        return self.jsonbody.get("phone_no", None)

    @property
    def event_time(self):
        datestring = "%s %s" % (
            self.jsonbody.get("event_date"),
            self.jsonbody.get("event_time"),
        )
        return datetime.strptime(datestring, "%Y-%m-%d %H:%M:%S")

    def order_number(self):
        return self.jsonbody.get("order_no", None)

    def order_status(self):
        return self.jsonbody.get("order_status", None)
