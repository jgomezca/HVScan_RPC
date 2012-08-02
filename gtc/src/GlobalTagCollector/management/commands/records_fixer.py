from django.core.management.base import BaseCommand
import os
import json
from GlobalTagCollector.models import Record, ObjectForRecords,SoftwareRelease
from GlobalTagCollector.utils.model_maps import ObjectRMap
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction




class Command(BaseCommand):
    help = 'Fix objects of records'

    def handle(self, *args, **options):
        """

        """
        curr_path = os.path.abspath(os.path.dirname(__file__))
        fixtures_path = os.path.join(curr_path,"..", "..", "fixtures")
        filename = os.path.join(fixtures_path, "records_fixture_list.json")
        file_data = open(filename,"rb").read()
        json_data = json.loads(file_data)

        obj_rcd_map = ObjectRMap()

        for record_name, container_name in json_data:
            obj_rcd = ObjectForRecords(name=container_name)
            obj_rcd = obj_rcd_map.get_or_insert(obj_rcd, False)

            try:
                record = Record.objects.get(name=record_name, object_r__name=container_name)
            except ObjectDoesNotExist :
                #we have to create new
                try:
                    with transaction.commit_on_success():
                        record = Record(name=record_name, object_r=obj_rcd)
                        record.save()
                        software_releases = SoftwareRelease.objects.filter(record__name=record_name)
                        if not len(software_releases):
                            software_releases = list(SoftwareRelease.objects.all())
                        record.software_release = software_releases
                except Exception as e:
                    logging.critical(e)
            else:
                #we already have this mapping
                pass


#
#            try:
#                rcd = Record.objects.get(name=record_name)
#                logging.info("Preparing to modify record: %s" % str(rcd.__dict__))
#                rcd.object_r=obj_rcd
#                rcd.save()
#            except Exception as e:
#                logging.critical(e)
#                logging.critical("Problem when executing record fix. %s %s" % (record_name,container_name))
#
