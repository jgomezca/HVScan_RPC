from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.aggregates import Count
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from GlobalTagCollector.libs.GTQueueManagement import GTQueueManager
from GlobalTagCollector.models import GTQueue, GTQueueEntry, GlobalTag
from django.contrib import messages

#TODO move to model forms
class GTQueueModelForm(ModelForm):
    class Meta:
        model = GTQueue

class GTQueueModelEditForm(GTQueueModelForm):
    class Meta:
        model = GTQueueModelForm.Meta.model
        exclude = ('last_gt','gt_account','gt_type_category')

@user_passes_test(lambda u: u.is_superuser)
def gt_queues_list(request):
    gt_queues = GTQueue.objects.all()
    return render_to_response("admin2/gt_queues_list.html", {"gt_queues": gt_queues}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def gt_queue_create(request):
    if request.method == 'POST':
        gt_queue_form = GTQueueModelForm(request.POST)
        if gt_queue_form.is_valid():
            with transaction.commit_on_success():
                gt_queue_obj = gt_queue_form.save()
                GTQueueManager(gt_queue_obj).create_children(request.user)
            return HttpResponseRedirect(reverse('gt_queue_list')) # Redirect after POST
    else:
        gt_queue_form = GTQueueModelForm()
    return render_to_response("admin2/gt_queue_create.html", {"gt_queue_form":gt_queue_form}, context_instance=RequestContext(request))


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
    GTQueueManager(queue).change_queue_entry_status(gt_queue_entry, new_status, request.user) #TODO needed GTQueueEntryManager

    messages.add_message(request, messages.INFO, "Queue entry with with record name "+gt_queue_entry.record.name+ "changed status to "+ new_status)
    return HttpResponseRedirect(reverse('gt_queue_entries', kwargs={'queue_id':queue.id})+"?entry_status_filter="+entry_status_filter)

@user_passes_test(lambda u: u.is_superuser)
def dashboard(request):
    global_tag_count = GlobalTag.objects.count()
    not_imported_global_tags = GlobalTag.objects.filter(has_errors=True)
    global_tag_queue_count = GTQueue.objects.all().count()
    global_tag_queue_pending_elements_count = GTQueueEntry.objects.filter(status="P").count()
    tb_name = GTQueueEntry()._meta.db_table
    open_queues = GTQueue.objects.filter(is_open=True).extra(
        select={'num_pending':
                    'SELECT COUNT(*) FROM {tb_name} WHERE ({tb_name}.status =\'P\') and ({tb_name}.queue_id = globaltagcollector_gtqueue.id)'.format(tb_name=tb_name)
        }
    )

    return render_to_response("admin2/dashboard.html", {
        'global_tag_count':global_tag_count,
        'global_tag_queue_count':global_tag_queue_count,
        'not_imported_global_tags':not_imported_global_tags,
        'global_tag_queue_pending_elements_count':global_tag_queue_pending_elements_count,
        'open_queues':open_queues,
        },
        context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def gt_info(request, gt_name):
    gt_obj = get_object_or_404(GlobalTag, name=gt_name)
    return render_to_response(
        "admin2/gt_info.html",
        {'gt_obj':gt_obj},
        context_instance=RequestContext(request)
    )