import logging
from django.core.management.base import BaseCommand
from columbine.workers import columbine_transaction_creator

logger = logging.getLogger("django_columbine.%s" % __name__)


class Command(BaseCommand):
    args = "none"
    help = "Management command to run the Columbine Transaction Creator. Runs once and exits."

    def handle(self, *args, **options):
        """
        The code is in columbine/workers/columbine_transaction_creator.py
        """
        columbine_transaction_creator.do_work()
