import logging
from django.core.management.base import BaseCommand
from columbine.workers import columbine_flow_creator

logger = logging.getLogger("django_columbine.%s" % __name__)


class Command(BaseCommand):
    args = "none"
    help = "Worker to create new Columbine Flows"

    def handle(self, *args, **kwargs):
        """
        The code is in columbine/workers/columbine_flow_creator.py
        """
        columbine_flow_creator.do_work()
