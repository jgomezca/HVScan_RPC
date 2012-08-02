from django.conf import settings
from django.core.management.base import BaseCommand
import urllib
from multiprocessing import Pool
from GlobalTagCollector.libs.data_update_managers import InitialGlobalUpdate


class Command(BaseCommand):


    def handle(self, *args, **options):
        InitialGlobalUpdate()._run()