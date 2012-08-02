from django.conf import settings
from django.core.management.base import BaseCommand
import urllib
from multiprocessing import Pool
from GlobalTagCollector.libs.data_update_managers import GlobalUpdate


class Command(BaseCommand):


    def handle(self, *args, **options):
        GlobalUpdate()._run()