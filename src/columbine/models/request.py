import logging

from django.db import models
from django.contrib.postgres.fields import JSONField

from columbine.models import ColumbineBaseModel

logger = logging.getLogger("django_columbine.%s" % __name__)


class Request(ColumbineBaseModel):
    """
    The Request model contains all HTTP requests with an FK to
    the Transaction which triggered it.
    """

    transaction = models.OneToOneField(
        "columbine.Transaction",
        on_delete=models.PROTECT,
        help_text="The Transaction this HTTP request was triggered by",
    )

    request_headers = JSONField(help_text="The HTTP request headers")

    request_body = models.TextField(help_text="The HTTP request POST body")

    response_status_code = models.IntegerField(
        blank=True, help_text="The HTTP status code returned by the Columbine API"
    )

    response_headers = JSONField(help_text="The HTTP response headers")

    response_body = models.TextField(help_text="The HTTP response body")
