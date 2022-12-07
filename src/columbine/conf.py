import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger("django_columbine.%s" % __name__)


class ColumbineSettingsBuilder:
    """
    All django-columbine settings are used through this module.

    Usage:

    from columbine.conf import columbine_settings
    print(columbine_settings.COLUMBINE_URL)
    """

    def __init__(self, *args, **kwargs):
        """
        Populate our columbine_settings module
        """
        if not hasattr(settings, "DJANGO_COLUMBINE"):
            raise ImproperlyConfigured("DJANGO_COLUMBINE not found in settings.py")

        # First get all settings the user specified in the normal django settings.py
        for setting in settings.DJANGO_COLUMBINE:
            setattr(self, setting, settings.DJANGO_COLUMBINE[setting])

        # Then get whatever we are missing from default_columbine_settings
        for setting in dir(ColumbineDefaultSettings):
            if setting not in dir(self):
                setattr(self, setting, getattr(ColumbineDefaultSettings, setting))

        # finally check if all the required settings are there
        for setting in ["COLUMBINE_URL"]:
            if not hasattr(self, setting):
                raise ImproperlyConfigured(
                    "settings.DJANGO_COLUMBINE['%s'] was not found. It is a required setting for django-columbine. Bailing out."
                    % setting
                )


class ColumbineDefaultSettings:
    """
    Default settings for django-columbine. Do not change anything here,
    set eg. DJANGO_COLUMBINE['XSD_COMMAND'] in settings.py instead.
    """

    XSD_COMMAND = "command.xsd"
    XSD_REPLY = "reply.xsd"
    XSD_NAMESPACES = {"xsd": "http://www.w3.org/2001/XMLSchema"}
    XSD_INCLUDE_XPATH = "//*/xsd:include[@schemaLocation]"

    # transaction types
    ORDER_VALIDATE = "order-validate"
    ORDER = "order"
    ORDER_ACK = "order-ack"
    RESCHEDULE_VALIDATE = "reschedule-order-validate"
    RESCHEDULE_ORDER = "reschedule-order"
    RESCHEDULE_ACK = "reschedule-ack"
    CANCEL_ORDER_VALIDATE = "cancel-order-validate"
    CANCEL_ORDER = "cancel-order"
    CANCEL_ORDER_ACK = "cancel-order-ack"
    DSLAM = "dslam"
    GET_EVENTS = "get-events"
    GET_EVENTS_ACK = "get-events-ack"
    GET_EVENT_STATUS = "get-event-status"
    SHOW_BROADBAND = "show-broadband"
    SHOW_CENTRAL = "show-central"
    SHOW_CUSTOMER_SUMMARY = "show_customer_summary"
    SHOW_NET_INFO = "show-net-info"
    SHOW_ORDER = "show-order"
    TRANSACTION_NAME_CHOICES = (
        (ORDER_VALIDATE, ORDER_VALIDATE),
        (ORDER, ORDER),
        (ORDER_ACK, ORDER_ACK),
        (RESCHEDULE_VALIDATE, RESCHEDULE_VALIDATE),
        (RESCHEDULE_ORDER, RESCHEDULE_ORDER),
        (RESCHEDULE_ACK, RESCHEDULE_ACK),
        (CANCEL_ORDER_VALIDATE, CANCEL_ORDER_VALIDATE),
        (CANCEL_ORDER, CANCEL_ORDER),
        (CANCEL_ORDER_ACK, CANCEL_ORDER_ACK),
        (DSLAM, DSLAM),
        (GET_EVENTS, GET_EVENTS),
        (GET_EVENTS_ACK, GET_EVENTS_ACK),
        (GET_EVENT_STATUS, GET_EVENT_STATUS),
        (SHOW_BROADBAND, SHOW_BROADBAND),
        (SHOW_CENTRAL, SHOW_CENTRAL),
        (SHOW_CUSTOMER_SUMMARY, SHOW_CUSTOMER_SUMMARY),
        (SHOW_NET_INFO, SHOW_NET_INFO),
        (SHOW_ORDER, SHOW_ORDER),
    )


# initiate our settings object
columbine_settings = ColumbineSettingsBuilder()
