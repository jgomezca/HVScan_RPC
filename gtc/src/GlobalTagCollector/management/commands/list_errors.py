
from django.core.management.base import BaseCommand

from GlobalTagCollector import models
import json
from GlobalTagCollector.models import GlobalTag


class Command(BaseCommand):


    def handle(self, *args, **options):
        errors = []
        for gt in GlobalTag.objects.filter(has_errors=True):
            errors_loaded = json.loads(gt.errors)
            errors += errors_loaded
        f = open('all_errors.txt',"wb")
        json.dump(errors,f, indent=4)
        f.close()