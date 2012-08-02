import datetime
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.query_utils import Q
from GlobalTagCollector.libs import utils
from GlobalTagCollector.models import GTType, ObjectForRecords, GTQueueEntry, GTQueue
from django.template import Context, Template

class GTQueueManager(object):

    def __init__(self, queue):
        self.queue_obj = queue

    def record_count(self):
        return self.queue_obj.gtqueueentry_set.all().count()

    def has_children(self):
        return bool(self.record_count())

    def create_children(self, administrator):
        if self.has_children():
            raise Exception("Queue allready fully created. Can not additionally insert children") #TODO custom exception

        now = datetime.datetime.now()
        with transaction.commit_on_success():
            for gt_record in self.queue_obj.last_gt.globaltagrecord_set.all():
                qte = GTQueueEntry()
                qte.queue = self.queue_obj
                qte.tag = gt_record.tag
                qte.record = gt_record.record
                qte.label = gt_record.label
                qte.comment = "Automaticaly created comment for original entries"
                qte.status = 'O'
                qte.submitter = administrator
                qte.administrator = administrator
                qte.administration_time = now
                qte.save()

    def _tag_object_is_related(self,  tag_obj, record_obj):
        return (tag_obj.object_r == record_obj.object_r) or (tag_obj.object_r.parent_name == record_obj.object_r.name)


    def _record_belongs_to_queue_software_release(self, record_obj):
        min_record_sw = record_obj.software_release.order_by('internal_version')[0].internal_version
        max_record_sw = list(record_obj.software_release.order_by('internal_version'))[-1].internal_version

        queue_min_sw = self.queue_obj.release_from.internal_version
        if self.queue_obj.release_to is not None:
            queue_max_sw = self.queue_obj.release_to.internal_version
        else:
            queue_max_sw = None

        return (queue_min_sw <= min_record_sw <= queue_max_sw) or \
               (queue_min_sw <= max_record_sw <= queue_max_sw) or \
               ((queue_min_sw <= max_record_sw) and (queue_max_sw is None))

    def list_of_afectable_records_by_status_change(self, record_obj, label, status):
        if (status=="O") or (status=="A"):
            return self.queue_obj.gtqueueentry_set.exclude(pk=record_obj.pk).filter(record=record_obj, label=label).filter(status__in=['O', 'A'])
        else:
            return self.queue_obj.gtqueueentry_set.none()

    def set_other_records_to_ignored(self, record_obj, label, status):
        afrecable_records = self.list_of_afectable_records_by_status_change(record_obj, label, status)
        afrecable_records.update(status='I')
        #TODO signal


    def add_queue_entry(self, tag_obj, record_obj, label, comment, submitter, administrator=None, status="P"): #status pending
        if not self._tag_object_is_related(tag_obj, record_obj):
            raise Exception("Tag and object is not related") #TODO custom exception
        if not self._record_belongs_to_queue_software_release(record_obj):
            raise Exception("Record does not match queue software release")

        now = datetime.datetime.now()
        qte = GTQueueEntry()
        qte.queue = self.queue_obj
        qte.tag = tag_obj
        qte.record = record_obj
        qte.label = label
        qte.comment = comment
        qte.submitter =     submitter
        qte.administrator = administrator
        qte.administration_time = now
        if (status=="P") or (status=="R") or (status=="I"):
            qte.status = status
            qte.save()
        elif (status=="O") or (status=="A"):
            print "STATUS O-A"
            with transaction.commit_on_success():
                self.set_other_records_to_ignored(record_obj, label, status)
                qte.status = status
                qte.save()

                #TODO signal
        else:
            raise Exception("Unknown gt queue record status")

    def change_queue_entry_status(self, queue_entry_obj, new_status, administrator):
        now = datetime.datetime.now()
        with transaction.commit_on_success():
            self.set_other_records_to_ignored(queue_entry_obj.record, queue_entry_obj.label, new_status)
            queue_entry_obj.status=new_status
            queue_entry_obj.administrator=administrator
            queue_entry_obj.administration_time = now
            queue_entry_obj.save()


#    def _compare_queue_and_gt_entry(self, queue_entry_obj, gt_entry_obj):
#        return (queue_entry_obj.record_id == queue_entry_obj.record_id) and \
#               (queue_entry_obj.label == queue_entry_obj.label)

    def update_queue_from_gt(self, gt_obj):
        same_queue_entries = [] #queue entries that exist in gt and in queue
        new_gt_entries = [] #new *gt entries* that was not founded in queue
        missed_queue_entries = [] #queue entries that wasnt founded in gt

        gt_entry_objects = gt_obj.globaltagrecord_set.all()
        gt_entry_objects_dict = {}
        gt_queue_entry_objects = self.queue_obj.gtqueueentry_set.all()
        gt_queue_entry_objects_dict = {}
        for gt_entry_object in gt_entry_objects:
            gt_entry_objects_dict[(gt_entry_object.record_id, gt_entry_object.label,)] = gt_entry_object
        for gt_queue_entry_object in gt_queue_entry_objects:
            gt_queue_entry_objects_dict[(gt_queue_entry_object.record_id, gt_queue_entry_object.label,)] = gt_queue_entry_object


        for gt_queue_entry_object in gt_queue_entry_objects:
            if gt_entry_objects_dict.has_key((gt_queue_entry_object.record_id, gt_queue_entry_object.label,)):
                #Queue and GT has the same entry
                same_queue_entries.append(gt_queue_entry_object)
            else:
                #Entry is in queue but not in GT
                missed_queue_entries.append(gt_queue_entry_object)
        for gt_entry_object in gt_entry_objects:
            if not gt_queue_entry_objects_dict.has_key((gt_entry_object.record_id, gt_entry_object.label,)):
                #entry is in gt, but not in queue
                new_gt_entries.append(gt_entry_object)

        #Now setting status to queue entries depending to witch list they belong
        all_queue_entries_with_status_changes = []
        with transaction.commit_on_success():
            for queue_entry in same_queue_entries:
                old_status = queue_entry.status
                new_status = utils.get_new_queue_entry_status(queue_entry.status,was_found_in_gt=True)
                queue_entry.status = new_status
                queue_entry.save()
                if old_status != new_status:
                    print queue_entry
                all_queue_entries_with_status_changes.append((old_status, new_status, queue_entry))



            for queue_entry in missed_queue_entries:
                old_status = queue_entry.status
                new_status = utils.get_new_queue_entry_status(queue_entry.status,was_found_in_gt=False)
                queue_entry.status = new_status
                queue_entry.save()
                all_queue_entries_with_status_changes.append((old_status, new_status, queue_entry))


            #new_queue_entries = []
            service_user, created = User.objects.get_or_create(username='gtc.service@cern.ch')
            for gt_entry in new_gt_entries:
                queue_entry = GTQueueEntry(
                    queue=self.queue_obj,
                    tag=gt_entry.tag,
                    record=gt_entry.record,
                    label=gt_entry.label,
                    comment='Found in GT',
                    status='O',
                    administrator=None,
                    submitter=service_user,
                    #todo - set in config default gt_entry_subbmiter and create it during instaltion
                    administration_time=None
                )
                queue_entry.save()
                all_queue_entries_with_status_changes.append((None, 'O', queue_entry))
                #self.new_queue_entries.append(queue_entry)


            #        return (
            #            self.same_queue_entries + self.missed_queue_entries + self.new_queue_entries,
            #            (self.same_queue_entries, self.missed_queue_entries, self.new_queue_entries)
            #            )

        return all_queue_entries_with_status_changes

#        def delete(self):
#        pass



    def queue_configuration(self):

        def strip_record_name(record_name):
            if record_name.endswith("Rcd"):
                return record_name[:-3]
            else:
                return record_name

        queue_obj = self.queue_obj

        template_str = """
{% autoescape off %}
[COMMON]
connect=sqlite_file:{{ gt_name }}.db
#connect={{ gt_account }}

[TAGINVENTORY]
tagdata=
{% for item_to_render in items_to_render %} {% if forloop.last %}{{ item_to_render.tag_name }}{pfn={{ item_to_render.pfn }},objectname={{ item_to_render.object_name }},recordname={{ item_to_render.record_name }}{% if item_to_render.label %},labelname={{item_to_render.label}}{% endif %}}{% else %}{{ item_to_render.tag_name }}{pfn={{ item_to_render.pfn }},objectname={{ item_to_render.object_name }},recordname={{ item_to_render.record_name }}{% if item_to_render.label %},labelname={{item_to_render.label}}{% endif %}};{% endif %}
{% endfor %}


[TAGTREE {{ expected_gt_name }}]
root=All
nodedata=Calibration{parent=All}
leafdata=
{% for item_to_render in items_to_render %} {% if forloop.last %}{{ item_to_render.record_name_stripped }}{{item_to_render.label}}{parent=Calibration,tagname={{ item_to_render.tag_name }},pfn={{ item_to_render.pfn }}}{% else %}{{ item_to_render.record_name_stripped }}{{item_to_render.label}}{parent=Calibration,tagname={{ item_to_render.tag_name }},pfn={{ item_to_render.pfn }}};{% endif %}
{% endfor %}

{% endautoescape %}
"""


        queue_entries = queue_obj.gtqueueentry_set.filter(Q(status='A') | Q(status='O')).select_related()

        items_to_render = []
        for gt_record in queue_entries:
            item_to_render = {'tag_name': gt_record.tag.name,
                              'record_name': gt_record.record.name,
                              'record_name_stripped': strip_record_name(gt_record.record.name)}
            pfn = GTType.objects.filter(gt_type_category=queue_obj.gt_type_category).filter(account_type=gt_record.tag.account.account_type)[0].type_conn_string + "/" +gt_record.tag.account.name
            item_to_render['pfn'] =  pfn
            item_to_render['object_name'] = gt_record.tag.object_r.name #ObjectForRecords.objects.get(tag=gt_record.tag, record=gt_record.record).name
            item_to_render['label'] = gt_record.label
            items_to_render.append(item_to_render)

        template = Template(template_string=template_str)
        c = Context({
            'gt_name':queue_obj.last_gt.name,
            'expected_gt_name': queue_obj.expected_gt_name,
            'gt_account':queue_obj.gt_account,
            'items_to_render':items_to_render})
        return template.render(c)


