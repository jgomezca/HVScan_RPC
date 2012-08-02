import collections
from django.db import transaction
from GlobalTagCollector.models import AccountType, Account, ObjectForRecords, Tag

class BaseModelMap(object):
    """

    """
    keys = None
    queryset = None

    def __init__(self):
        if not isinstance(self.keys, collections.Iterable):
            raise Exception("Keys should be iterable (list or tuple)")

        self._container = {}
        self._delayed_saving_list = []

        if self.queryset is not None:
            self.insert(*list(self.queryset))

    def _get_item_key(self, item):
        return tuple([item.__dict__[key] for key in self.keys])

    def _insert_item(self, item):
        key = self._get_item_key(item)
        self._container[key] = item

    def insert(self, *items):
        """

        """
        for item in items:
            self._insert_item(item)

    def get(self, key, default=None):
        """

        """
        return self._container.get(key, default)

    def get_or_insert(self, item, delayed=True):
        """

        """
        key = self._get_item_key(item)
        catched_item = self._container.get(key, None)
        if catched_item is not None:
            return catched_item
        if not delayed:
            item.save()
            self._container[key] = item
            return item
        else:
            self._delayed_saving_list.append(item)
            self._container[key] = item
            return item

    def process_delayed(self):
        """

        """
        with transaction.commit_on_success():
            for item in self._delayed_saving_list:
                item.save()
            self._delayed_saving_list = []



class AccountTypeMap(BaseModelMap):
    keys = ['title',]
    queryset = AccountType.objects.all()

class AccountMap(BaseModelMap):
    keys = ['name','account_type_id']
    queryset = Account.objects.all()

class ObjectRMap(BaseModelMap):
    keys = ['name',]
    queryset = ObjectForRecords.objects.all()


class TagMap(BaseModelMap):
    keys = ['name','account_id', 'object_r_id']
    queryset = Tag.objects.all()