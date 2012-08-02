
from django.core.management.base import BaseCommand

from GlobalTagCollector import models
import json
from GlobalTagCollector.models import GlobalTag


class Command(BaseCommand):


    def handle(self, *args, **options):
        errors = []
        for gt in GlobalTag.objects.filter(has_errors=True):
            errors_loaded = json.loads(gt.errors)
            #for el errors_loaded
            errors += errors_loaded
#        igts = models.IgnoredGlobalTag.objects.all()
#        errors = []
#        account_errors = []
#        tag_errors = []
#        record_errors = []
#        for igt in igts:
#            errors_loaded = json.loads(igt.reason)
#            errors.append(errors_loaded)
#            if len(errors_loaded.get('tag_errors',[]))!=0:
#                tag_errors.append(errors_loaded['tag_errors'])
#            if len(errors_loaded.get('account_errors',[]))!=0:
#                account_errors.append(errors_loaded['account_errors'])
#            if len(errors_loaded.get('record_errors',[]))!=0:
#                record_errors.append(errors_loaded['record_errors'])

#        f = open('account_errors.txt',"wb")
#        json.dump(account_errors,f, indent=4)
#        f.close()
#
#        f = open('tag_errors.txt',"wb")
#        json.dump(tag_errors,f, indent=4)
#        f.close()
#
#        f = open('record_errors.txt',"wb")
#        json.dump(record_errors,f, indent=4)
#        f.close()

        f = open('all_errors.txt',"wb")
        json.dump(errors,f, indent=4)
        f.close()