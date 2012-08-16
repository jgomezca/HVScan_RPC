from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext as _
from GlobalTagCollector.managers import ImportedGTByDate


class ServiceData(models.Model):
    '''
    Abstract model, that each model should inherit if it takes data from services. It is used to store information
    about manual changes of service information (if data entry was added or ignored manually).
    '''

    class Meta:
        abstract = True

    entry_manual_added = models.BooleanField(default=False, help_text="Was this entry added manually?")
    entry_ignored = models.BooleanField(default=False, help_text="Was this entry ignored manually due to some problems?")
    entry_administrator = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_administrator", null=True, blank=True, help_text="Administrator, who edited this entry")
    entry_comment = models.TextField(blank=True, help_text="Reson, why this entry was edited")
    entry_creation_date = models.DateTimeField(auto_now_add=True, help_text="When entry was inserted?")
    entry_editing_date = models.DateTimeField(auto_now=True, help_text="When entry was modified?")
    entry_ignoring_canceled = models.DateTimeField(null=True, blank=True, help_text="If was ignored, when ignoring was canceled.")


class AccountType(ServiceData):
    '''List of all known account types'''

    class Meta:
        ordering = ['visible_for_users', 'name', 'title']
    title = models.CharField(max_length=200, unique=True, blank=False)
    name = models.CharField(max_length=200, unique=True, blank=False)
    connection_string = models.CharField(max_length=200,  unique=True, blank=True, null=True)
    visible_for_users = models.BooleanField(default=False)
    use_in_gt_import  = models.BooleanField(default=True)

    def save(self, force_insert=False, force_update=False, using=None):
        if self.connection_string == "":
            self.connection_string = None
        return super(AccountType, self).save(force_insert, force_update, using)

    def clean(self):
        if (self.connection_string == "" or self.connection_string is None) and self.visible_for_users:
            raise ValidationError("Account can not be saved. It can be visible for users, when there is value of conn_string")

    def __unicode__(self):
        return self.title


    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "title__icontains", "connection_string__icontains",


class Account(ServiceData):
    """Defines model for managing accounts (of tags & records)"""

    class Meta:
        unique_together = (
            ("name", "account_type"),
        )

    name = models.CharField(max_length=200)
    account_type = models.ForeignKey(AccountType)
    use_in_gt_import  = models.BooleanField(default=True)
    #tags_list_hash is used to monitor if tags for account has changed in remote services
    tags_list_hash = models.TextField(max_length=40, blank=True, db_index=True, help_text="Storing hash tag list page")

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

    def related_label(self):
        return u"%s - %s " % (self.name, self.account_type.title, ) #is it bug, becuase shows id?



class HardwareArchitecture(ServiceData):
    """List of architecures for which software is avaibable"""

    name = models.CharField(blank=False, max_length=200, unique=True, help_text=_("Name of hardware achitecture"))

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",


class SoftwareRelease(ServiceData):
    """CMSSW software relases"""

    class Meta:
        ordering = ['internal_version',]

    name = models.CharField(blank=False, max_length=200, unique=True, help_text=_("Name of CMS_SW release"))
    internal_version = models.IntegerField(unique=True, help_text=_("Helps to compare CMS_SW relase versions"))
    hardware_architecture = models.ManyToManyField(HardwareArchitecture)
    records_updated = models.BooleanField(default=False)

    def get_major_version(self):
        return self.internal_version / 100000000
    major_version = property(get_major_version)

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",


class ObjectForRecords(ServiceData):
    """Object and record mapping"""

    name = models.CharField(blank=False, max_length=200, unique=True,
                            help_text=_("Object related with a Tag (helps to get a record)"))
    parent_name = models.CharField(blank=True, max_length=200, unique=False,
        help_text=_("Object related with a Tag (helps to get a record)"))

    def __unicode__(self):
        return self.name


    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

class Record(ServiceData):
    """Record of a tag"""

    class Meta:
        unique_together = (("object_r", "name",),)
        ordering = ['name', "object_r"]

    object_r = models.ForeignKey(ObjectForRecords)
    name = models.CharField(blank=False, max_length=200)
    software_release = models.ManyToManyField(SoftwareRelease)

    def tags(self):
        return Tag.objects.filter(object_r__id=self.object_r.id)

    def __unicode__(self):
        return self.name


    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",


class Tag(ServiceData):
    """Tag bellonging to the account"""
    #TODO add fields to tag model
#    #mayby should be moved to in separate table
#    #deleted = models.BooleanField(default=False)
#    #ready_for_deletion = models.BooleanField(default=False)

    class Meta:
        unique_together = (("account", "name", "object_r"),)

    name = models.CharField(blank=False, max_length=200, )
    account = models.ForeignKey(Account)
    object_r = models.ForeignKey('ObjectForRecords')

    def __unicode__(self):
        return self.name

    def records(self):
        return Record.objects.filter(object_r__id=self.object_r.id)

    def related_label(self):
        return u"%s (%s) < %s < %s" % (self.name, self.id, self.account.name, self.account.account_type.title)

    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

class GlobalTagRecordValidationError(ValidationError):
    def __init__(self, tag, record):
        message = "Record does not belong to the tag. "
        message += "Tag id: {{tag_id}}, Tag name: {{tag_name}}."
        message += "Record id:{{record_id}}, Record name:{{record_name}}. "
        msg = message.format(tag_id=tag.id, tag_name=tag.name, record_id=record.id, record_name=record.name)
        super(GlobalTagRecordValidationError, self).__init__(msg)


class GlobalTag(ServiceData):
    """Global tag names"""

    class Meta:
           ordering = ('name',  )


    name = models.CharField(blank=False, max_length=100, unique=True, help_text=_("Name of a global tag"))
 #   created_externally = models.BooleanField(help_text=_("Is it found in external services? (Not created with admin)"))
    external_finding_timestamp = models.DateTimeField(null=True, help_text=_("When global tag was found in webservices"))
    internal_creation_timestamp = models.DateTimeField(null=True, help_text=_("When administrator created global tag"))
    creator = models.ForeignKey(User, null=True, help_text=_("Administrator who created Global Tag (if any)"))

    warnings = models.TextField(blank=True)
    errors = models.TextField(blank=True)

    has_warnings = models.BooleanField(default=True)
    has_errors = models.BooleanField(default=True)

    objects = models.Manager()
    imported = ImportedGTByDate()

    def __unicode__(self):
        return self.name



    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

#    def add_active_records_from_queue(self, queue): #FIX transactional
#        for item in queue.active_items():
#            gtr = GTRecord(
#                    global_tag=self,
#                    tag=item.tag,
#                    record=item.record,
#                    label=item.label
#                    ).save()


class GlobalTagRecord(models.Model):
    """Records belonging to Global Tag"""

    class Meta:
    #        verbose_name = "GT Item"
        unique_together = (
        ("global_tag", "tag", "record", "label"),
        )

    global_tag = models.ForeignKey(GlobalTag)
    tag = models.ForeignKey(Tag)
    record = models.ForeignKey(Record)
    label = models.CharField(blank=True, max_length=200)
    pfn = models.CharField(blank=True, max_length=400)
    #TODO consistency check frontier_connection = models.CharField(blank=False, max_length=100) #Leave for consistency check

    def clean(self):
        if not (self.tag.object_r == self.record.object_r) or (self.tag.object_r.parent_name == self.record.object_r.name):
            #raise ValidationError('Record does not belong to the tag')
            raise GlobalTagRecordValidationError(self.tag, self.record)

    def __str__(self):
        return "GT:%s Tag:%s Container:%s Record:%s label:%s" % (self.global_tag.name, self.tag.name, self.tag.object_r.name, self.record.name, self.label)

#------------------------------------------------------------------------------

class GTAccount(models.Model):
    """Global tags has also an accounts. Here is list of them"""

    #    class Meta:
    #        verbose_name = "GT Account"

    name = models.CharField(blank=False, max_length=200, unique=True, help_text=_("Account of global tag"))

    def deletable(self):
        print self.gtqueue_set.count()
        return self.gtqueue_set.count() == 0

    def __unicode__(self):
        return self.name


    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

class GTTypeCategory(models.Model):
    """Category of a global tag type. E.g. mc, offline. tier0, online"""

    name = models.CharField(blank=False, max_length=200, unique=True)

    def deletable(self):
        return (self.gtqueue_set.count() == 0) and (self.gttype_set.count()==0)


    def __unicode__(self):
        return self.name


    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains",

class GTType(models.Model):
    """(GTType description)"""

    #    class Meta:
    #        verbose_name = "GT Type"


    gt_type_category = models.ForeignKey(GTTypeCategory)
    type_conn_string = models.CharField(blank=False,
                                        max_length=400) #!can not be unique #is it woth to extract to separate table?
    account_type = models.ForeignKey(AccountType) #shoud be filter , bot tu mix queue records from one account with other account

    def deletable(self):
        return True #it seems all the time deletable

    def __unicode__(self):
        return "%s %s [%s...]" % (self.gt_type_category.name, self.account_type.title, self.type_conn_string[:25])



    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "type_conn_string__icontains",


class GTQueue(models.Model):
    """Queue for new Global Tags"""

#    class Meta:
#        verbose_name = "Queue"
#        verbose_name_plural = "Queues"

    name = models.CharField(blank=False, max_length=100, unique=True, help_text=_("Name of Global Tag Queue"))
    description = models.TextField(blank=True)
    is_open = models.BooleanField(default=True)
    last_gt = models.ForeignKey(GlobalTag)
    gt_account = models.ForeignKey(GTAccount)
    #gt_type = models.ForeignKey(GTType)
    gt_type_category = models.ForeignKey(GTTypeCategory)

    release_from = models.ForeignKey(SoftwareRelease, related_name="relase_from")
    release_to = models.ForeignKey(SoftwareRelease, related_name="relase_to", null=True, blank=True)

    expected_gt_name = models.CharField(null=True, blank=True, max_length=100, unique=True, help_text=_("Expected global tag name"))

    def clean(self):
        if (self.release_to is not None) and (self.release_from.internal_version > self.release_to.internal_version):
            raise ValidationError('Release to must be None or internal version must be not smaller than Relase from')

    def save(self, force_insert=False, force_update=False, using=None):
        if (self is not None) and (self.expected_gt_name == ""):
            self.expected_gt_name = None
        q = super(GTQueue, self).save(force_insert, force_update, using)


#
    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return "id__iexact", "name__icontains", "description__icontains",

class GTQueueEntry(models.Model):
    """(QueueTagEntry description)"""

    class Meta:
            permissions = (
                ("can_requeue", "Can requeue element from ne queue to another"),
            )

    STATUS_CHOICES = (
    ('O', 'Original'), #when creating new queue or after creating GT from queue
    ('P', 'Pending'), # not allowed from original.
    ('A', 'Approved'), #from pending only
    ('R', 'Rejected'), #from Pending only. #can we set rejected from approved or viea versa?
    ('I', 'Ignored'), #Ignore == changed. property owervritetten by other property
    #('F', 'Replaced') #when original was not found
    )

    queue = models.ForeignKey(GTQueue)
    tag = models.ForeignKey(Tag)
    record = models.ForeignKey(Record)
    label = models.CharField(blank=True, max_length=1200)
    comment = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    submitter = models.ForeignKey(User, related_name="gtentries_submited")
    administrator = models.ForeignKey(User, null=True, related_name="gtentries_managed") #ASK null true or blank true for foreign keys
    submitting_time = models.DateTimeField(auto_now_add=True)
    administration_time = models.DateTimeField(null=True, blank=True)

    __original_status = None

    def __init__(self, *args, **kwargs):
        super(GTQueueEntry, self).__init__(*args, **kwargs)
        self.__original_status = self.get_status_display()

    def save(self, force_insert=False, force_update=False, using=None):
        """original and accepted values becomes ignored when inserted new """

        print self.__original_status, self.get_status_display()
        #skip_save = False #for the following hack
        if self.__original_status:
            if self.get_status_display() != self.__original_status:
                pass
                #now hack from http://stackoverflow.com/questions/1555060/how-to-save-a-model-without-sending-a-signal
               # GTQueueEntry.objects.filter(id=self.id).update(**self.__dict__)
               # skip_save = True


        #if not skip_save:
        r = super(GTQueueEntry, self).save()
        self.__original_status = self.get_status_display()
        if self.status == 'A': #should be record already inseted
           self.queue.gtqueueentry_set.exclude(pk=self.pk).filter(record=self.record, label=self.label).filter(status__in=['O', 'A']).update(status='I')
        return r

    def safe_to_change(self):
        return GTQueueEntry.objects.filter(queue=self.queue, record=self.record, label=self.label ).count() <=1

    def __str__(self):
        return "(%s) Tag:%s,  Record:%s, Label:%s" % (self.status, self.tag.name, self.record.name, self.label )
