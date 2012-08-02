
from django.core.management.base import BaseCommand

from GlobalTagCollector import models
import json
from GlobalTagCollector.libs.GTQueueManagement import GTQueueManager
from GlobalTagCollector.models import GlobalTag, GTQueue


class Command(BaseCommand):


    def handle(self, *args, **options):
        print GTQueueManager().queue_configuration(GTQueue.objects.get(name="START52_V9_K1"))