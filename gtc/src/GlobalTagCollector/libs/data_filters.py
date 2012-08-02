# coding=utf-8
import itertools
from GlobalTagCollector.models import Account, Tag, Record, GlobalTag, IgnoredGlobalTag, IgnoredAccount

class AccountFilter(object):

    def leave_not_existing(self, accounts):
        not_existing_accounts = []
        existing_accounts_set = set(Account.objects.values_list('account_type__title','name'))
        for account in accounts:
            account_tuple = (account["account_type"], account["account_name"])
            if not (account_tuple in existing_accounts_set):
                not_existing_accounts.append(account)
        return not_existing_accounts


class TagsFilter(object):

    def leave_not_existing(self, account, tags_containers):
        not_existing_tag_containers  = []
        existing_tag_containers = set(Tag.objects.filter(account=account).values_list('name','object_r__name'))
        for tag_container in tags_containers:
            tag_container_tuple = tag_container["tag_name"], tag_container["container_name"]
            if not (tag_container_tuple in existing_tag_containers):
                not_existing_tag_containers.append(tag_container)
        return not_existing_tag_containers


class SoftwareReleaseFilter(object):

    def leave_not_existing(self,hardware_architecture_obj, software_release_names):
        db_release_names = set([name[0] for name in hardware_architecture_obj.softwarerelease_set.values_list('name')])
        new_release_names_set = set(software_release_names) - db_release_names
        return new_release_names_set

class RecordsFilter(object):

    def __init__(self):
        self.record_release_name_set = set(Record.objects.values_list('name','software_release__name'))

    def leave_not_existing(self, release_obj, record_container_map):
        software_release_name = release_obj.name
        not_existing_record_container_map = {}
        for recod_name in record_container_map.keys():
            record_release_tuple = (recod_name, software_release_name)
            if record_release_tuple not in self.record_release_name_set:
                not_existing_record_container_map[recod_name] = record_container_map[recod_name]
        return not_existing_record_container_map

class GlobalTagListFilter(object):

    def leave_not_existing(self, global_tag_names):
        db_gt_names = set([name for (name,) in GlobalTag.objects.filter(has_errors=False).values_list('name')])#error
        ignored_gt_names = set([name for (name,) in IgnoredGlobalTag.objects.filter(is_ignored=False).values('name')])
        return set(global_tag_names) - db_gt_names - ignored_gt_names

class GlobalTagEntriesFilter(object):

    def _entry_is_ignored(self, gt_entry):
        return (gt_entry["pfn"]=="frontier://FrontierPrep/CMS_COND_30X_HCAL") and \
               (gt_entry["label"]=="") and \
               (gt_entry["tag"]== "HcalCholeskyMatrices_v1.01_mc") and \
               (gt_entry["record"]=="HcalCholeskyMatricesRcd")

    def not_ignored_entries(self, gt_entires):
        return list(itertools.ifilterfalse(self._entry_is_ignored, gt_entires))

    def entries_with_errors(self, gt_entires):
        return list(itertools.ifilter(lambda x: x.has_key('exceptions'), gt_entires))

    def entries_without_errors(self, gt_entires):
        return list(itertools.ifilterfalse(lambda x: x.has_key('exceptions'), gt_entires))

#    def leave_allowed_account_type_titles(self, gt_entries): #required resolved acc types
#        ignored_account_type_titles = ['Archive','Offline integration']
#        f = lambda gt_entry: gt_entry["account_type_obj"].title in ignored_account_type_titles
#        return list(itertools.ifilterfalse(f, gt_entries))
#
#    def leave_not_allowed_account_type_titles(self, gt_entries): #required resolved acc types
#        ignored_account_type_titles = ['Archive','Offline integration']
#        f = lambda gt_entry: gt_entry["account_type_obj"].title in ignored_account_type_titles
#        return list(itertools.ifilter(f, gt_entries))

#    def leave_allowed_accounts(self, entries_with_allowed_account_types):
#        ignored_account_names = [obj.account.name for obj in IgnoredAccount.objects.all()] #todo check by account type
#        print ignored_account_names
#        rez = []
#        for gt_entry in entries_with_allowed_account_types:
#            account_name = gt_entry['pfn'].rsplit("/", 1)[1]
#            if account_name in ignored_account_names:
#                print "skipping", account_name
#                continue
#            rez.append(gt_entry)
#        return rez
#
#    def leave_not_allowed_accounts(self, entries_with_allowed_account_types):
#        ignored_account_names = [obj.account.name for obj in IgnoredAccount.objects.all()]
#        rez = []
#        for gt_entry in entries_with_allowed_account_types:
#            account_name = gt_entry['pfn'].rsplit("/", 1)[1]
#            if account_name not in ignored_account_names:
#                continue
#            rez.append(gt_entry)
#        return rez