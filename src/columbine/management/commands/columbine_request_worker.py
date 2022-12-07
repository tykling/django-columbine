import logging
from django.core.management.base import BaseCommand
from columbine.workers import columbine_request_worker

logger = logging.getLogger("django_columbine.%s" % __name__)


class Command(BaseCommand):
    args = "none"
    help = "Worker to create and run Columbine Requests"

    def handle(self, *args, **kwargs):
        """
        The code is in columbine/workers/columbine_request_worker.py
        """
        columbine_request_worker.do_work()
