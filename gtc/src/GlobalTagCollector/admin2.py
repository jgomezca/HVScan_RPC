from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from GlobalTagCollector import reports
from GlobalTagCollector.libs.GTQueueManagement import GTQueueManager
from GlobalTagCollector.libs.GTSettings import *
from GlobalTagCollector.models import GTQueue, GTQueueEntry, GlobalTag, GTType, SoftwareRelease, Record_Software_Release, Record, ObjectForRecords
from GlobalTagCollector.forms import HardwareArchitectureModelForm
from django.contrib import messages
import logging
from django.core.exceptions import MultipleObjectsReturned

logger = logging.getLogger(__file__)

#TODO move to model forms
from GlobalTagCollector.reports import report_queue_created

class GTQueueModelForm(ModelForm):
    class Meta:
        model = GTQueue

    def __init__(self, *args, **kwargs):
        super(GTQueueModelForm, self).__init__(*args, **kwargs)
        if 'last_gt' in self.fields.values():
            self.fields['last_gt'].queryset = GlobalTag.objects.filter(entry_ignored=False)

class GTQueueModelEditForm(GTQueueModelForm):
    class Meta:
        model = GTQueueModelForm.Meta.model
        exclude = ('last_gt','gt_account','gt_type_category')

@user_passes_test(lambda u: u.is_superuser)
def gt_queues_list(request):
    queue_status = request.GET.get('filter_queue_status', "open")
    gt_queues = GTQueue.objects.all()
    if queue_status == "all":
        pass
    elif queue_status=="closed":
        gt_queues = gt_queues.filter(is_open=False)
    else: #open
        gt_queues = gt_queues.filter(is_open=True)
        queue_status = "open"
    return render_to_response("admin2/gt_queues_list.html", {"gt_queues": gt_queues, "fqs":queue_status}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def gt_queue_create(request):
    if request.method == 'POST':
        gt_queue_form = GTQueueModelForm(request.POST)
        if gt_queue_form.is_valid():
            with transaction.commit_on_success():
                gt_queue_obj = gt_queue_form.save()
                GTQueueManager(gt_queue_obj).create_children(request.user)
                logger.info("Preparing for report")
                report_queue_created(gt_queue_obj)
                logger.info("Report should be sent")
            return HttpResponseRedirect(reverse('gt_queue_list')) # Redirect after POST
    else:
        gt_queue_form = GTQueueModelForm()
    return render_to_response("admin2/gt_queue_create.html", {"gt_queue_form":gt_queue_form}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def gt_queue_clone(request, queue_id):
    ''' Clone an existing queue and its entries via GTQueueManager class '''
    gt_queue_obj = get_object_or_404(GTQueue, pk=queue_id)
    cloned_queue_obj = GTQueueManager(gt_queue_obj).queue_clone()

    return HttpResponseRedirect(reverse('gt_queue_edit', kwargs={'queue_id':cloned_queue_obj.id}))

@user_passes_test(lambda u: u.is_superuser)
def gt_queue_edit(request, queue_id):
    gt_queue = get_object_or_404(GTQueue, pk=queue_id)
    if request.method == 'POST':
        gt_queue_form = GTQueueModelEditForm(request.POST, instance=gt_queue)
        if gt_queue_form.is_valid():
            gt_queue_form.save()
            return HttpResponseRedirect(reverse('gt_queue_list'))
    else:
        gt_queue_form=GTQueueModelEditForm(instance=gt_queue)
    return render_to_response("admin2/gt_queue_edit.html", {"gt_queue":gt_queue,"gt_queue_form":gt_queue_form}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def gt_queue_entries(request, queue_id):
    def filter_query_by_entry_status(query, status_filter=''):
        if status_filter == "ALL":
            return query
        if not status_filter:
            return query.filter(status='P')
        return query.filter(status=status_filter)
    entry_status_filter = request.GET.get('entry_status_filter','P')
    gt_queue = get_object_or_404(GTQueue, pk=queue_id)
    gt_queue_entries_qs = gt_queue.gtqueueentry_set.all()
    gt_queue_entries_qs = filter_query_by_entry_status(gt_queue_entries_qs, entry_status_filter)
    gt_queue_entries_qs = gt_queue_entries_qs.select_related()

    #Each gt_queue_entry append with attribute type_conn_string
    #TODO: improve query to avoid 1+N db queries
    for gt_queue_entry in gt_queue_entries_qs:
        try:
            type_conn_string = GTType.objects.get(gt_type_category=gt_queue.gt_type_category, account_type=gt_queue_entry.tag.account.account_type).type_conn_string
        except MultipleObjectsReturned:
            # Fix for the HLT queue entries, where MultipleObjectsReturned may be raised
            type_conn_string = GTType.objects.filter(gt_type_category=gt_queue.gt_type_category, account_type=gt_queue_entry.tag.account.account_type)[0].type_conn_string
        gt_queue_entry.type_conn_string = type_conn_string

    return render_to_response("admin2/gt_queue_entries.html", {
        "gt_queue":gt_queue,
        "gt_queue_entries":gt_queue_entries_qs,
        "entry_status_filter":entry_status_filter},
        context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def gt_queue_entry_status_change(request, gt_queue_entry_id, new_status):
    gt_queue_entry = get_object_or_404(GTQueueEntry, pk=gt_queue_entry_id)
    entry_status_filter = request.GET.get('entry_status_filter','')
    queue = gt_queue_entry.queue
    change_results = GTQueueManager(queue).change_queue_entry_status(gt_queue_entry, new_status, request.user) #TODO needed GTQueueEntryManager

    queue_entry_obj, affected_records, old_status, old_status_display = change_results
    reports.report_queue_entry_status_changed(queue_entry_obj, affected_records, old_status, old_status_display)

    messages.add_message(request, messages.INFO, "Queue entry with with record name "+gt_queue_entry.record.name+ "changed status to "+ new_status)
    return HttpResponseRedirect(reverse('gt_queue_entries', kwargs={'queue_id':queue.id})+"?entry_status_filter="+entry_status_filter)

@user_passes_test(lambda u: u.is_superuser)
def gt_queue_entry_multiple_status_change(request, gt_queue_id, new_status):
    ''' Queue entries multiple status change '''
    entry_status_filter = request.GET.get('entry_status_filter', '')
    queue_pending_entries = GTQueueEntry.objects.filter(queue_id=gt_queue_id,status='P')

    if queue_pending_entries:
        for e in queue_pending_entries:
            gt_queue_entry = get_object_or_404(GTQueueEntry, pk=e.id)
            queue = gt_queue_entry.queue
            change_results = GTQueueManager(queue).change_queue_entry_status(gt_queue_entry, new_status, request.user)
            queue_entry_obj, affected_records, old_status, old_status_display = change_results
            reports.report_queue_entry_status_changed(queue_entry_obj, affected_records, old_status, old_status_display)
            messages.add_message(request, messages.INFO, "Queue entry with record name " + gt_queue_entry.record.name + " changed multiple entries status to " + new_status)

    return HttpResponseRedirect(reverse('gt_queue_entries', kwargs={'queue_id':gt_queue_id})+"?entry_status_filter="+entry_status_filter)

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    global_tag_count = GlobalTag.objects.filter(entry_ignored=False).count()
    not_imported_global_tags = GlobalTag.objects.filter(entry_ignored=False, has_errors=True)
    inconsistent_global_tags_count = GlobalTag.objects.filter(entry_ignored=False, has_warnings=True).count()
    global_tag_queue_count = GTQueue.objects.all().count()
    global_tag_queue_pending_elements_count = GTQueueEntry.objects.filter(status="P").count()
    tb_name = GTQueueEntry()._meta.db_table
    open_queues = GTQueue.objects.filter(is_open=True).extra(
        select={'num_pending':
                    'SELECT COUNT(*) FROM {tb_name} WHERE ({tb_name}.status =\'P\') and ({tb_name}.queue_id = globaltagcollector_gtqueue.id)'.format(tb_name=tb_name)
        }
    )

    return render_to_response("admin2/dashboard.html", {
        'global_tag_count': global_tag_count,
        'global_tag_queue_count': global_tag_queue_count,
        'not_imported_global_tags': not_imported_global_tags,
        'inconsistent_global_tags_count': inconsistent_global_tags_count,
        'global_tag_queue_pending_elements_count': global_tag_queue_pending_elements_count,
        'open_queues': open_queues,
        },
        context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def gt_settings(request):
    template_vars = {}

    form_submitted = False

    section = request.GET.get('section') if request.GET.get('section') else 'hwa'
    if section == 'hwa':
        hwa_settings_obj = HardwareArchitectureSettings()
        template_vars.update(hwa_settings_obj.init_form())
        if request.method == 'POST':
            form_submitted = hwa_settings_obj.insert_hwa(request.POST)
        elif request.GET.get('del_hwa'):
            hwa_settings_obj.delete_hwa(request.GET.get('del_hwa'))
    elif section == 'gtc':
        gts_settings_obj = GlobalTagSettings()
        template_vars.update(gts_settings_obj.init_form())
        if request.method == 'POST':
            form_submitted = gts_settings_obj.update_gtc(request.POST.get('gt'), 1)
        elif request.GET.get('gt'):
            form_submitted = gts_settings_obj.update_gtc(request.GET.get('gt'), False)
    elif section == 'acc':
        acc_settings_obj = AccountSettings()
        template_vars.update(acc_settings_obj.init_form())
        if request.method == 'POST':
            form_submitted = acc_settings_obj.insert_acc(request.POST)
        elif request.GET.get('del_acc'):
            acc_settings_obj.delete_acc(request.GET.get('del_acc'))

    template_vars['form_submitted'] = form_submitted
    return render_to_response("admin2/gt_settings.html", template_vars, context_instance=RequestContext(request))
