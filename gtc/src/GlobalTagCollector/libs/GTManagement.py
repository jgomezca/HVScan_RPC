import json
from django.db.models.query_utils import Q
from GlobalTagCollector.libs.GTQueueManagement import GTQueueManager
from GlobalTagCollector.libs.data_filters import GlobalTagEntriesFilter
from GlobalTagCollector.libs.exceptions import TagNotDetectedException, RecordNotDetectedException, AccountTypeNotFoundedForPFNBase, AccountNotFoundedException, RawGTEntryIgnoredException
from GlobalTagCollector.models import GTType, Account, Tag, Record, GlobalTagRecord, GlobalTag, ObjectForRecords, GTQueue
from django.db.transaction import commit_on_success

class RawGTEntry(object):

    def __init__(self, raw_dict, gt_obj=None):
        self.raw_dict = raw_dict
        self.gt_obj = gt_obj
        self.is_ignored = False
        self.ignoring_reason = None
        self.has_error = False
        self.error = None
        self.tag_container = None
        self.record_containers = None
        self.records_with_name = None

    def _parse_pfn(self):
        """Splitting pfn to pnf base and accont name. Pfn updated to new version if needed"""
        #TODO validate pfn format
        pfn = self.raw_dict["pfn"] ##possible key error
        self.pfn_base, self.account_name = pfn.rsplit("/", 1)

    def _replace_pfn(self):
        """Old Pfn (that is not used or valid) is replaced to new new if needed"""
        old_pfn = "frontier://(proxyurl=http://localhost:3128)(serverurl=http://localhost:8000/FrontierOnProd)(serverurl=http://localhost:8000/FrontierOnProd)(retrieve-ziplevel=0)"
        new_pfn = "frontier://(proxyurl=http://localhost:3128)(serverurl=http://localhost:8000/FrontierOnProd)(serverurl=http://localhost:8000/FrontierOnProd)(retrieve-ziplevel=0)(failovertoserver=no)"
        if self.pfn_base == old_pfn:
            self.pfn_base = new_pfn


    def _find_account_type(self):
        rez_list = list(GTType.objects.filter(type_conn_string=self.pfn_base)[:1])
        if rez_list:
            self.account_type_obj = rez_list[0].account_type
        else:
            raise AccountTypeNotFoundedForPFNBase(self.pfn_base)

    def _find_if_account_type_is_importable(self):
        if not self.account_type_obj.use_in_gt_import:
            raise RawGTEntryIgnoredException(
                "Account Type %s should not be used while importing GTs" % self.account_type_obj
            )

    def _find_is_account_is_importable(self):
        try:
            self.account_obj = Account.objects.get(account_type=self.account_type_obj, name=self.account_name)
            if not self.account_obj.use_in_gt_import:
                raise RawGTEntryIgnoredException("Account %s should not be used while importing GTs" % self.account_obj)
        except (Account.DoesNotExist, Account.MultipleObjectsReturned) as e: #multiple should be never raised
            raise AccountNotFoundedException(self.account_type_obj, self.account_name)

    def _find_tag(self):
        tag_name = self.raw_dict['tag'] #possible key error
        try:
            self.tag_obj = Tag.objects.get(name=tag_name, account=self.account_obj)
        except (Tag.DoesNotExist, Tag.MultipleObjectsReturned) as e: #multiple should not raise
            raise TagNotDetectedException(tag_name, self.account_type_obj, self.account_name, e)


    def _find_record(self):
        record_name = self.raw_dict['record'] #possible key error
        try:
            #regular search
            self.record_obj = Record.objects.get(object_r__tag=self.tag_obj,name = record_name)
        except (Record.DoesNotExist, Record.MultipleObjectsReturned) as e:
            #search by parent
            try:
                tag_container_parent = self.tag_obj.object_r.parent_name
                self.record_obj = Record.objects.get(object_r__name=tag_container_parent,name = record_name)#TODO - put warning
            except Record.DoesNotExist:
                raise RawGTEntryIgnoredException("Could not detect record with name %s which belongs to tag %s" % (record_name, self.tag_obj))



    def resolve(self):
        try:
            self._parse_pfn()
            self._find_account_type()
            self._find_if_account_type_is_importable()
            self._find_is_account_is_importable()
            self._find_tag()
            self._find_record()
        except RawGTEntryIgnoredException as e:
            self.is_ignored = True
            self.ignoring_reason = str(e)
        except (AccountTypeNotFoundedForPFNBase, AccountNotFoundedException,TagNotDetectedException, RecordNotDetectedException) as e:
            self.has_error = True
            self.error = str(e)
        self.is_valid = not self.is_ignored and not self.has_error

    def dict_for_json(self):
        data = self.raw_dict
        #data["time"] = data["time"]
        if self.tag_container:
            tag_container_value = {'main':self.tag_obj.object_r.name, 'parent':self.tag_obj.object_r.parent_name}
        else:
            tag_container_value = None

        if self.record_containers:
            record_container_value = [{'main':container.name, 'parent':container.parent_name} for container in self.record_containers]
        else:
            record_container_value = None

        return {
            'data': data,
            'has_error': self.has_error,
            'error': self.error,
            'is_ignored': self.is_ignored,
            'ignoring_reason': self.ignoring_reason,
            'tag_container': tag_container_value,
            'record_containers': record_container_value,
            'records_with_name': self.records_with_name,
        }

    def get_gt_record_object(self):
        return GlobalTagRecord(
            global_tag = self.gt_obj,
            tag = self.tag_obj,
            record = self.record_obj,
            label = self.raw_dict["label"],
            pfn = self.pfn_base+"/"+self.account_name
        )

class RawGT(object):
    def __init__(self, gt_dict):
        self.gt_dict = gt_dict
        self.raw_gt_entries = []

    def resolve(self):
        self.name = self.gt_dict['GlobalTagName']
        for global_tag_entry in self.gt_dict['global_tag_entries']:
            raw_gt_entry = RawGTEntry(global_tag_entry)
            raw_gt_entry.resolve()
            self.raw_gt_entries.append(raw_gt_entry)

    def has_errors(self):
        error_exists = False
        for raw_gt_entry in self.raw_gt_entries:
            error_exists = error_exists or raw_gt_entry.has_error
        return error_exists

    def has_warnings(self):
        warnings_exists = False
        for raw_gt_entry in self.raw_gt_entries:
            warnings_exists = warnings_exists or raw_gt_entry.is_ignored
        return warnings_exists

    def _entries_to_dicts_list(self, entries):
        dicts_list = []
        for entry in entries:
            dicts_list.append(entry.dict_for_json())
        return dicts_list

    def entries_dicts_list(self):
        return self._entries_to_dicts_list(self.raw_gt_entries)

    def entries_with_errors(self):
        bad_entries = []
        for raw_gt_entry in self.raw_gt_entries:
            if raw_gt_entry.has_error:
                bad_entries.append(raw_gt_entry)
        return bad_entries

    def entries_with_errors_dict(self):
        return self._entries_to_dicts_list(self.entries_with_errors())

    def entries_ignored(self):
        ignored_entries = []
        for raw_gt_entry in self.raw_gt_entries:
            if raw_gt_entry.is_ignored:
                ignored_entries.append(raw_gt_entry)
        return ignored_entries

    def entries_ignored_dict(self):
        return self._entries_to_dicts_list(self.entries_ignored())

    def entries_valid(self):
        valid_entries = []
        for raw_gt_entry in self.raw_gt_entries:
            if raw_gt_entry.is_valid :
                valid_entries.append(raw_gt_entry)
        return valid_entries

    def entries_valid_dict(self):
        return self._entries_to_dicts_list(self.entries_valid())

    def valid_entry_objects(self, gt_obj=None):
        rez = []
        for valid_entry in self.entries_valid():
            gt_record_object = valid_entry.get_gt_record_object()
#            if gt_obj is not None:
#                gt_record_object.global_tag = gt_obj
            rez.append(gt_record_object)
        return rez

    def _set_children_gt(self, gt_obj):
        for raw_gt_entry in self.raw_gt_entries:
            raw_gt_entry.gt_obj = gt_obj

    def save(self):
        #TODO if was errors
        with commit_on_success():
            gt_obj, created = GlobalTag.objects.get_or_create(name=self.name)
            if not gt_obj.has_errors:
                raise Exception("Trying to save already correctly saved GT")
            #print self.name, "was created: ", created
            gt_obj.has_errors = self.has_errors()
            if self.has_errors():
                gt_obj.errors = json.dumps(self.entries_with_errors_dict(), indent=4)
            else:
                gt_obj.errors = ""

            gt_obj.has_warnings = self.has_warnings()
            if self.has_warnings():
                gt_obj.warnings = json.dumps(self.entries_ignored_dict(), indent=4)
            else:
                gt_obj.warnings = ""

            gt_obj.save()
            if not self.has_errors():
                self._set_children_gt(gt_obj)
                valid_entries = self.valid_entry_objects(gt_obj)

                new_valid = []

                for e in range(0, len(valid_entries)):
                    obj_exists = GlobalTagRecord.objects.filter(global_tag_id=valid_entries[e].global_tag, tag_id=valid_entries[e].tag, record_id=valid_entries[e].record, label=valid_entries[e].label)
                    if obj_exists:
                        obj_exists = False
                    else:
                        new_valid.append(valid_entries[e])

                valid_entries = new_valid

                for i in range(0, len(valid_entries), 50):
                    GlobalTagRecord.objects.bulk_create(valid_entries[i:i+50])

                try:
                    gt_queue_obj = GTQueue.objects.get(expected_gt_name=gt_obj.name)
                    GTQueueManager(gt_queue_obj).update_queue_from_gt(gt_obj)
                except GTQueue.DoesNotExist:
                    pass




#            not_ignored_entries = GlobalTagEntriesFilter().not_ignored_entries(gt_dict['global_tag_entries'])#
#    entries_for_saving = self._prepare_gt_entries_for_saving(gt, entries_with_records_without_errors)
