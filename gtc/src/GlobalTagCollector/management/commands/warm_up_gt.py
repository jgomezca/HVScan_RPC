from __future__ import division
from django.core.management.base import BaseCommand

from GlobalTagCollector import models
from GlobalTagCollector.libs import data_providers
from GlobalTagCollector.libs.data_providers import GlobalTagProvider

import json
from multiprocessing import Pool
import sys



def f(gt_name):
    try:
        provider = GlobalTagProvider()
        provider.provide(gt_name)
    except Exception as e:
        pass


class Command(BaseCommand):

    def handle(self, *args, **options):

        p = Pool(30)

        gts = data_providers.GlobalTagListProvider()._provide()
        num_tasks = len(gts)
        print gts
        print "Mapping"
        for i, _ in enumerate(p.imap_unordered(f, gts)):
            sys.stderr.write('\rdone {0:%}'.format(i/num_tasks))


        print "Mapped. Waiting for result"
        #r.wait()
        print "Result got"
