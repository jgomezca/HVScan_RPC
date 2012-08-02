from django.conf import settings
from django.core.management.base import BaseCommand
from globalify.GlobalTagCollector.reports import report_yesterday_global_tags, report_last_7_days_global_tags

class Command(BaseCommand):


    def handle(self, *args, **options):
        #report_yesterday_global_tags()
        email_thread = report_last_7_days_global_tags()
