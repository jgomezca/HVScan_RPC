# coding=utf-8
import datetime
import pprint
from django.contrib.auth.models import User
from django.db import transaction
import django.db.transaction
from GlobalTagCollector.libs.GTManagement import RawGTEntry, RawGT
from GlobalTagCollector.libs.data_filters import GlobalTagEntriesFilter
from GlobalTagCollector.libs.data_providers import GlobalTagProvider
#from GlobalTagCollector.management.commands.global_tags_update import change_status
from GlobalTagCollector.models import AccountType, Account, ObjectForRecords, Tag, Record, SoftwareRelease, GlobalTag, GlobalTagRecord, GTQueueEntry
from GlobalTagCollector.libs.exceptions import RecordNotDetectedException, TagNotDetectedException
import GlobalTagCollector.models
import utils


class AccountTypeObjectsCreator(object):
    def _create_objects(self, dblist):
        rez = []
        for db_dict in  dblist:
            (at, at_created) = AccountType.objects.get_or_create(
                                    name=db_dict["DBID"],
                                    defaults={
                                        'title': db_dict["DB"],
                                        'connection_string': None,
                                        'visible_for_users': False,
                                    }
                                )
            rez.append((at, at_created))
        return rez


class AccountObjectCreator(object):
    def _create_objects(self, account_type_obj, accounts):
        rez = []

        for account in accounts:
            (acc, acc_created) = Account.objects.get_or_create(name=account, account_type = account_type_obj)
            rez.append((acc, acc_created))
        return rez


class TagObjectCreator(object):

    def _create_objects(self, account, tags_containers):
        rez = []
        for tag_container in tags_containers:
            (o4r, o4r_created) = ObjectForRecords.objects.get_or_create(name=tag_container["container_name"])
            (tag, tag_created) = Tag.objects.get_or_create(
                name=tag_container["tag_name"],
                object_r=o4r,
                account=account)
            rez.append((tag, tag_created))
        return rez


class SoftwareReleaseCreator():

    def _create_objects(self, hardware_architecture_obj, software_release_names):
        rez = []
        for software_release_name in software_release_names: #todo possible but it seems not necessary to use transactions
            sr_version_number = utils.software_release_name_to_version(software_release_name)
            if sr_version_number % 1000 != 999:
                continue #because it is prerelease
            (sr, sr_created) = SoftwareRelease.objects.get_or_create(name=software_release_name, internal_version=sr_version_number)
            sr.hardware_architecture.add(hardware_architecture_obj)
            rez.append((sr, sr_created))
        return rez


class RecordObjectCreator(object):

    def _create_objects(self, release_obj, filtered_record_container_map):
        rez = []
        for record_name, container_name in filtered_record_container_map.items():
            with transaction.commit_on_success():
                (container_obj, co_created) = ObjectForRecords.objects.get_or_create(name=container_name)
                (record_obj, r_created) = Record.objects.get_or_create(name=record_name, object_r=container_obj)
                release_obj.record_set.add(record_obj)
                release_obj.save()
                rez.append((record_obj, r_created))
        return rez



#DELETE ?
class GlobalTagQueuePreparer(object):

    def __init__(self, queue_obj, prepared_gt):
        self.queue_for_update_obj = queue_obj
        self.prepared_gt = prepared_gt

        self.current_queue_entries_dict = {}
        for queue_entry in self.queue_for_update_obj.gtqueueentry_set.all():
            self.current_queue_entries_dict[ (queue_entry.record_id, queue_entry.label) ] = queue_entry

        self.same_queue_entries = [] #queue entries that exist in gt and in queue
        self.new_gt_entries = [] #new *gt entries* that was not founded in queue
        self.missed_queue_entries = [] #queue entries that wasnt founded in gt
        self.new_queue_entries = []

    def _queue_and_gt_records_groups(self):
        """
        list entries existing in gt and queue
        """
        for gt_record in self.prepared_gt["gt_records"]:
            queue_entry = self.current_queue_entries_dict.pop((gt_record.record_id, gt_record.label),None)
            if queue_entry:
                self.same_queue_entries.append(queue_entry)
            else:
                self.new_gt_entries.append(gt_record)
        self.missed_queue_entries = self.current_queue_entries_dict.values()


    def _prepare_queue_entries(self):
        self._queue_and_gt_records_groups()
        for queue_entry in self.same_queue_entries:
            queue_entry.status = utils.get_new_queue_entry_status(queue_entry.status,was_found_in_gt=True)

        for queue_entry in self.missed_queue_entries:
            queue_entry.status = utils.get_new_queue_entry_status(queue_entry.status,was_found_in_gt=False)


        for gt_entry in self.new_gt_entries:
            queue_entry = GTQueueEntry(
                queue=self.queue_for_update_obj,
                tag=gt_entry.tag,
                record=gt_entry.record,
                label=gt_entry.label,
                comment='Found in GT',
                status='O',
                administrator=None,
                submitter=User.objects.get(username='gtc.service@cern.ch'),
                        #todo - set in config default gt_entry_subbmiter and create it during instaltion
                        #fix raises exception when not founded
                administration_time=None
            )
            self.new_queue_entries.append(queue_entry)

        return (
            self.same_queue_entries + self.missed_queue_entries + self.new_queue_entries,
            (self.same_queue_entries, self.missed_queue_entries, self.new_queue_entries)
        )



class GTCreatorQueueUpdater(object):

    def _save(self, prepared_gt, queue_obj=None, queue_entries=None):
        with transaction.commit_on_success():
            prepared_gt['gt_obj'].save()
            for gt_record in prepared_gt['gt_records']:
                gt_record.global_tag = prepared_gt['gt_obj']
                gt_record.save()
            if queue_entries:
                for queue_entry in queue_entries:
                    queue_entry.save()
                queue_obj.last_gt = prepared_gt['gt_obj']
                queue_obj.expected_gt_name=None
                queue_obj.save()


class QueueObjectCreator(object):
    def create_queue_entries_from_gt(self, queue, administrator):
        now = datetime.datetime.now()

        with transaction.commit_on_success():
            for gt_record in queue.last_gt.globaltagrecord_set.all():
                qte = GTQueueEntry()
                qte.queue = queue
                qte.tag = gt_record.tag
                qte.record = gt_record.record
                qte.label =gt_record.label #ASK PFN
                qte.comment = "Automaticaly created comment for original entries" #ASK maybe global tag entires should have
                qte.status = 'O'
                qte.submitter = administrator
                qte.administrator = administrator
                qte.administration_time = now
                qte.save()
                #todo detect if success