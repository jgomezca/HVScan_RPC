import datetime, time
import json
import django
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models.aggregates import Count
from django.db.models.query_utils import Q
from django.forms.models import ModelForm

from django.http import  HttpResponseForbidden
from django.template.context import RequestContext
from django.template import Context, Template
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.decorators import login_required, permission_required

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from GlobalTagCollector import reports
from GlobalTagCollector.libs.GTQueueManagement import GTQueueManager
from models import *
from django.http import HttpResponse, HttpResponseRedirect
import forms
from django.contrib.auth.decorators import login_required

import logging
from django.shortcuts import  render_to_response

logger = logging.getLogger().setLevel(logging.DEBUG) #todo update name


def int_or_zero(val):
    """

    """
    try:
        return int(val)
    except ValueError:
        return 0

@login_required
def to_json(obj_dics):
    """

    """
    result = {
        'response_status': 'ok',
        'data':obj_dics
    }
    return HttpResponse(json.dumps(result), mimetype="application/json")

@login_required
def json_account_types(request):
    objects = AccountType.objects.filter(visible_for_users=True).order_by('title')
    obj_dics = [{'id': obj.id, 'name':obj.title} for obj in objects]
    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")

@login_required
def json_accounts(request):
    objects = Account.objects.filter(account_type=int_or_zero(request.GET.get('parent', None)), account_type__visible_for_users=True).order_by('name')
    obj_dics = [{'id': obj.id, 'name':obj.name} for obj in objects]
    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")

@login_required
def json_tags(request):
    objects = Tag.objects.filter(account=int_or_zero(request.GET.get('parent', None))).order_by('name')
    obj_dics = [{'id': obj.id, 'name':obj.name} for obj in objects]
    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")

@login_required
def json_records(request): #TODO try except
    tag = Tag.objects.get(pk=int_or_zero(request.GET.get('parent', None)))
    objects = Record.objects.filter(object_r__tag=tag).all()
    obj_dics = [{'id': obj.id, 'name':obj.name} for obj in objects]
    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")

@login_required
def json_queues_for_record(request): #TODO try except
    """

    """
    record = Record.objects.get(pk=int_or_zero(request.GET.get('parent', None)))
    record_releases = list(record.software_release.all().order_by('internal_version'))
    lowest_internal_version = record_releases[0].internal_version
    higest_internal_version = record_releases[-1].internal_version
    #TODO hardware arch
    queue_list = GTQueue.objects.filter(is_open=True).filter(release_from__internal_version__lte=higest_internal_version).filter(Q(release_to__internal_version__gte=lowest_internal_version) | Q(release_to=None)).order_by('name')
    obj_dics = [{'id': obj.id, 'name':obj.name, 'descr':obj.description } for obj in queue_list] #obj.description
    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")

@login_required
def json_warnings_gt(request):
    """ Fetch GT import warnings if any """
    warn = GlobalTag.objects.get(pk=int_or_zero(request.GET.get('gt_id', None)))
    obj_dict = json.loads(warn.warnings) if warn.warnings else {'no_warnings': 'True'}
    return HttpResponse(json.dumps(obj_dict), mimetype="application/json")

#--------------
@login_required
def list_view(request):
    """

    """
    logging.debug("hello world!")
    logging.warn("Working with user %s" % request.user)
    user_submits_list = GTQueueEntry.objects.filter(submitter=request.user).order_by('-submitting_time').select_related(depth=1)
    status = request.GET.get('status',"All")
    if status in ('A', 'R', 'P', 'O', 'I'):
        user_submits_list = user_submits_list.filter(status=status)

    date_filter = request.GET.get('date', 'all')


    start_date = None
    end_date = None
    if date_filter == 'today':
        start_date = datetime.date.today()
        end_date = datetime.date.today()
    elif date_filter == "yesterday":
        start_date = datetime.date.today() - datetime.timedelta(1)
        end_date = datetime.date.today()  - datetime.timedelta(1)
    elif date_filter == "week":
        start_date = datetime.date.today() - datetime.timedelta(weeks=1)
        end_date = datetime.date.today()
    elif date_filter == "month" :
        start_date = datetime.date.today() - datetime.timedelta(weeks=4)
        end_date = datetime.date.today()
    elif date_filter == "older_than_month" :
        end_date = datetime.date.today() - datetime.timedelta(weeks=4)


    if (start_date is not None) and (end_date is not None):
        user_submits_list = user_submits_list.filter(
            Q(submitting_time__range=(
                datetime.datetime.combine(start_date, datetime.time.min),
                datetime.datetime.combine(end_date, datetime.time.max))
             ) |
            Q(administration_time__range=(
                datetime.datetime.combine(start_date, datetime.time.min),
                datetime.datetime.combine(end_date, datetime.time.max))
             ))
    elif (start_date is None) and (end_date is not None):
        user_submits_list = user_submits_list.filter(
            Q(submitting_time__lte=datetime.datetime.combine(end_date, datetime.time.max)) |
            Q(administration_time__lte=datetime.datetime.combine(end_date, datetime.time.max)) )

    #deffereing because of oracle error
    queue_list = GTQueue.objects.defer('description').filter(gtqueueentry__submitter=request.user).distinct().order_by('name') # active and users

   
    checked_queues = request.GET.getlist('queue')
    if len(checked_queues) == 1 and checked_queues[0] == u'':
        checked_queues = []

    
    new_checked_queues = []
    for element in checked_queues:
        try:
            number = int(element)
            new_checked_queues.append(number)
        except Exception:
            pass
    new_checked_queues = filter(lambda x:x>0, new_checked_queues)
    checked_queues = new_checked_queues
    if len(checked_queues):
        user_submits_list = user_submits_list.filter(queue__id__in=checked_queues)
    
    paginator = Paginator(user_submits_list, 25)
    page = request.GET.get('page', 1)
    try:
        user_submits = paginator.page(page)
    except PageNotAnInteger:
        user_submits = paginator.page(1)
    except EmptyPage:
        user_submits = paginator.page(paginator.num_pages)
        
    return render_to_response(
        "submits_list.html",
            {'user_submits':user_submits.object_list,
             'page':user_submits, 'date':date_filter,
             'paginator':user_submits,
             'status':status,
             'queue_list':queue_list,
             'checked_queues':checked_queues},
        context_instance=RequestContext(request))

@login_required
def details_view(request, id):
    """

    """
    entry = get_object_or_404(GTQueueEntry,id=id)
    if (entry.submitter != request.user) and (not request.user.is_superuser):
        return HttpResponseForbidden('Not enough permissions')
    return render_to_response("details_view.html", {'entry':entry}, context_instance=RequestContext(request))

@login_required
def tag_list(request):
    ''' Quick access to all available tags and for a given GT '''
    template_vars = {}

    distinct_tags_all = False

    gt_id = request.GET.get('gt')
    if gt_id:
        distinct_tags = GlobalTagRecord.objects.filter(global_tag_id=gt_id).select_related(depth=1).values('record__name','tag__name')
    else:
        distinct_tags = Tag.objects.all().values('name').distinct()
        distinct_tags_all = True

    if request.GET.get('download'):
        if distinct_tags_all:
            response_template = '''{% for t in distinct_tags %}{{ t.name }}{% if not forloop.last %}\n{% endif %}{% endfor %}'''
            filename = "GTC_tags_%s.txt" % int(time.time())
        else:
            response_template = '''{% for t in distinct_tags %}{{ t.tag__name }}{% if not forloop.last %}\n{% endif %}{% endfor %}'''
            filename = "%s_tags_%s.txt" % (GlobalTag.objects.get(pk=gt_id).name, int(time.time()))
            
        template = Template(template_string=response_template)
        c = Context({'distinct_tags': distinct_tags})

        response = HttpResponse(template.render(c))
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response

    gt_obj_list = GlobalTag.objects.all().filter(entry_ignored=False)
    template_vars["gt_obj_list"] = gt_obj_list


    paginator = Paginator(distinct_tags, 25) # Show 25 tags per page
    page = request.GET.get('page')
    try:
        tags = paginator.page(page)
    except PageNotAnInteger:
        tags = paginator.page(1)
    except EmptyPage:
        tags = paginator.page(paginator.num_pages)
    
    if distinct_tags_all:
        template_vars["distinct_tags_all"] = True
    template_vars["distinct_tags"] = tags
    template_vars["distinct_tags_count"] = len(distinct_tags)

    return render_to_response("admin2/tag_list.html", template_vars, context_instance=RequestContext(request))

@login_required
@ensure_csrf_cookie
def new_request(request):
    request.META["CSRF_COOKIE_USED"] = True 
    if request.is_ajax():
        formset = forms.QueueTagEntryFormSet(request.POST)
        if formset.is_valid():
#            import pdb; pdb.set_trace()
            formset_rez = formset.save(request.user) #try except save error
            reports.report_queue_entry_submitted(formset_rez) #list of entries, because one entry for each queue
            return HttpResponse(json.dumps({'form':'OK', 'errors':[]}) )
        else:
            errors = formset.errors
            return HttpResponse(json.dumps({'form':'FAILED', 'errors':errors}))
    else:
        return render_to_response("new_request.html", {}, context_instance=RequestContext(request))


def record_container_map(request):
    hardware_architecture_name = request.GET.get("hardware_architecture_name")
    software_release_name = request.GET.get("software_release_name")
    rez = {'body' : {"record_container_map": []}}
    sr = SoftwareRelease.objects.get(name=software_release_name, hardware_architecture__name=hardware_architecture_name)
    records = sr.record_set.all().select_related().order_by("name", "object_r__name")
    for record in records:
        rez["body"]["record_container_map"].append( {
            "container": record.object_r.name,
            "record_name": record.name
        })
    return HttpResponse(json.dumps(rez), mimetype="application/json")


#create  form gt queue entry
class RequeueForm(ModelForm):
    class Meta:
        model = GTQueueEntry
#        widgets = {
#                    'queue': autocomplete_formfield(User.permissions),
#                }


@permission_required('gt_queue_entry.can_requeue')
def requeue_entry(request,gtentry_id=None):
    """

    """
    f = RequeueForm()
    return HttpResponse("<table>"+str(f)+"</table>")


@login_required
def gt_conf_export(request, gt_queue_name):
    queue = get_object_or_404( GTQueue, name=gt_queue_name)
    response_text = GTQueueManager(queue).queue_configuration()
    filename = queue.expected_gt_name + ".conf"

    response = HttpResponse(response_text)
    response['Content-Disposition'] = 'attachment; filename=' + filename
    return response

def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(request.GET.get('next','/'))

    user = authenticate(request=request)
    if (user is None) and (settings.PRODUCTION_LEVEL == "private"):

        user = User.objects.get_or_create(
            username = "DevelopmentUser",
            defaults = dict(
                first_name = "DummyFirstName",
                last_name = "DummyFirstName",
                email = "Dummy@example.com",
                password = django.contrib.auth.hashers.make_password("dummypsw"),
                is_active = True,
                is_staff = True,
                is_superuser = True
            )
        )[0]
        #user.save()
        user = authenticate(username="DevelopmentUser", password="dummypsw")

    if user is None:
        return HttpResponseForbidden("User could not be authenticated")
    else:
        if not request.user.is_authenticated():
            django.contrib.auth.login(request, user)
        return HttpResponseRedirect(request.GET.get('next','/'))#TODO better path

def admin2_logout(request):
    from django.contrib.auth import logout
    from django.http import HttpResponseRedirect
    logout(request)
    return HttpResponseRedirect('https://login.cern.ch/adfs/ls/?wa=wsignout1.0')

class ShibbolethBackend(object):

    def _get_username(self, request):
        return request.META.get('HTTP_ADFS_LOGIN')

    def _get_full_name(self, request):
        return request.META.get('HTTP_ADFS_FULLNAME')

    def _get_groups(self, request):
        return request.META.get('HTTP_ADFS_GROUP','').split(';')

    def _get_first_name(self, request):
        return request.META.get('HTTP_ADFS_FIRSTNAME')

    def _get_last_name(self, request):
        return request.META.get('HTTP_ADFS_LASTNAME')

    def _get_adfs_email(self, request):
        return request.META.get('HTTP_ADFS_EMAIL')



    def authenticate(self, request):
        #Must have headers - if they are, then it is possible to authenticate
        print "auth"
        import pprint
        pprint.pprint(request.META)

        if self._get_full_name(request) is None:
            return None
        print "auth1"
        if self._get_full_name(request) is None:
            return None
        print "auth2"
        if self._get_groups(request) is None:
            return None
        print "auth3"

        is_staff = settings.ADMIN_GROUP_NAME in self._get_groups(request)
        is_superuser = is_staff

        try:
            user = User.objects.get(username=self._get_username(request))
            #updating current user
            user.first_name = self._get_first_name(request),
            user.last_name = self._get_last_name(request),
            user.email = self._get_adfs_email(request),
            user.password = "",
            user.is_active = True,
            user.is_staff = is_staff,
            user.is_superuser = is_superuser
            user.save()
            return user
        except User.DoesNotExist:
            user = User.objects.get_or_create(
                username = self._get_username(request),
                first_name = self._get_first_name(request),
                last_name = self._get_last_name(request),
                email = self._get_adfs_email(request),
                password = "",
                is_active = True,
                is_staff = is_staff,
                is_superuser = is_superuser

            )
            return user[0]




    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
