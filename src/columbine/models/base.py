import logging
import uuid

from django.db import models

logger = logging.getLogger("django_columbine.%s" % __name__)


class ColumbineBaseModel(models.Model):
    """
    This abstract base model is used for all the other django-columbine
    models. We use UUID as primary keys and offer a created_date and
    modified_date field for convenience.
    There is also a "tag" property which returns something like
    Flow#22eb859e-e71e-4406-bf3a-83f002995423 and is returned as the
    default string representation of the model instance.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )

    created_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="The date and time this object was created",
    )

    modified_date = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="The date and time this object was last modified",
    )

    class Meta:
        abstract = True
        ordering = ["-created_date"]

    @property
    def tag(self):
        return "%s#%s" % (self.__class__.__name__, self.pk)

    def __str__(self):
        return self.tag
