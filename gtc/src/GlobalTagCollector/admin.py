try:
    from django.conf.urls import patterns, url, include #django 1.4
except:
    from django.conf.urls.defaults import  patterns, url, include #django 1.3.1
from django.shortcuts import  render_to_response
from django.template.context import RequestContext
from django.db.models.aggregates import Count
import logging
from django.conf import settings
import datetime
from django.core.urlresolvers import reverse
from urllib import urlencode
from django.forms.models import BaseModelForm
from django.http import Http404
from django.shortcuts import get_object_or_404
import django
from django.utils import html
from django.db.models import Q
from django.contrib import admin
from GlobalTagCollector.libs.data_inserters import QueueObjectCreator
#from GlobalTagCollector.management.commands.gt_problems import global_tag_problems
from GlobalTagCollector.libs.admin import DetailsViewMixin
from GlobalTagCollector import models
from django.core.cache import cache
from django.forms import ModelChoiceField

logger = logging.getLogger(__name__)
admin.site.disable_action('delete_selected')



class GTAccountAdmin(admin.ModelAdmin):
    #todo add page listing queues containing chosen GT Account
    list_display = ('name', 'link_to_delete_gtaccount',)
    list_display_links = ('link_to_delete_gtaccount',)

    def has_add_permission(self, request):
        """

        """
        return True


    def has_change_permission(self, request, obj=None):
        """

        """
        return  obj is None


    def link_to_delete_gtaccount(self, obj): #TODO icon reqired
        """

        """
        print dir(obj)
        if obj.deletable():
            url = reverse('admin:GlobalTagCollector_gtaccount_delete', args=(obj.id,))
            return "<a href='%s'>[X] Delete %s</a>" % (url, html.escape(obj.name))
        return ""
    link_to_delete_gtaccount.allow_tags = True
    link_to_delete_gtaccount.admin_order_field = 'id'
    link_to_delete_gtaccount.short_description = 'Delete'


    def has_delete_permission(self, request, obj=None):
        """

        """
        return (obj is None) or (obj.gtqueue_set.count() == 0)


class GTTypeCategoryAdmin(admin.ModelAdmin):
    #todo add page listing queues containing chosen GT type category
    list_display = ('name', 'link_to_delete_gttypecategory')
    list_display_links = ('link_to_delete_gttypecategory',)

    def has_add_permission(self, request):
        """

        """
        return True


    def has_change_permission(self, request, obj=None):
        """

        """
        return  obj is None


    def link_to_delete_gttypecategory(self, obj): #TODO icon reqired
        """

        """
        if obj.deletable():
            url = reverse('admin:GlobalTagCollector_gttypecategory_delete', args=(obj.id,))
            return "<a href='%s'>[X] Delete %s</a>" % (url, html.escape(obj.name))
        return ""
    link_to_delete_gttypecategory.allow_tags = True
    link_to_delete_gttypecategory.admin_order_field = 'id'
    link_to_delete_gttypecategory.short_description = 'Delete'

    def has_delete_permission(self, request, obj=None):
        """

        """
        return (obj is None) or (obj.deletable())


class GTTypeAdmin(admin.ModelAdmin):
    list_display = ['gt_type_category', 'type_conn_string', 'link_to_account_type','link_to_delete_gttype']
    list_display_links = ['link_to_account_type']

    def has_add_permission(self, request):
        """

        """
        return True


    def has_change_permission(self, request, obj=None):
        """

        """
        return  obj is None

    def has_delete_permission(self, request, obj=None):
        """

        """
        return (obj is None) or (obj.deletable())

    def link_to_delete_gttype(self, obj): #TODO icon reqired
        """

        """
        if obj.deletable():
            url = reverse('admin:GlobalTagCollector_gttype_delete', args=(obj.id,))
            return "<a href='%s'>[X] Delete </a>" % (url,)
        return ""
    link_to_delete_gttype.allow_tags = True
    link_to_delete_gttype.admin_order_field = 'id'
    link_to_delete_gttype.short_description = 'Delete'

    def link_to_account_type(self, obj): #TODO icon reqired
        """

        """
        url = reverse('admin:GlobalTagCollector_accounttype_change', args=(obj.account_type.id,))
        return "<a href='%s'> %s</a>" % (url,html.escape(obj.account_type.title))
    link_to_account_type.allow_tags = True
    link_to_account_type.admin_order_field = 'id'
    link_to_account_type.short_description = 'Account type'

from django.contrib.admin.widgets import AdminURLFieldWidget
from django.utils.safestring import mark_safe
class URLFieldWidget(AdminURLFieldWidget):
    def render(self, name, value, attrs=None):
        """

        """
        widget = super(URLFieldWidget, self).render(name, value, attrs)
        return mark_safe(u'%s<input type="button" '
                         u'value="Requeue" onclick="window.'
                         u'open(document.getElementById(\'%s\')'
                         u'.value)" />' % (widget, attrs['id']))

#class WaitingListForm(django.forms.ModelForm):
#    class Meta:
#        model = models.GTWaitingList

class GTQueueEntryInlineForm(django.forms.ModelForm):


    """

"""

    class Meta:
        model = models.GTQueueEntry

    requeue = django.forms.CharField(label='Requeue', required=False, widget=URLFieldWidget())
    save_to_change = django.forms.BooleanField(required=False,label="Safe to change",help_text="Same tag recod lable exists in this queue?")
    def __init__(self, *args, **kwargs):
        super(GTQueueEntryInlineForm, self).__init__(*args, **kwargs)
        #print self.save(commit=False)
       # print "args", args
        print "kwargs jj", kwargs
        if kwargs.has_key("instance"):
            self.fields['requeue'].initial="/admin/globaltagcollector/gtqueueentry/add/?requeue_id=%d" % kwargs["instance"].id
            self.fields['requeue'].widget.attrs['readonly'] = True
            self.fields['requeue'].widget.attrs['style'] = "display: none;"
            self.fields['save_to_change'].widget.attrs['disabled'] = "disabled"
            self.fields['save_to_change'].initial =   (kwargs["instance"].tc != 1) #kwargs["instance"].safe_to_change()
            print self.fields.keys()
        else:
            pass
#            self.fields['administrator'].widget.attrs['style'] = "display: none;"
#            self.fields['administration_time'].widget.attrs['style'] = "display: none;"
            #self.fields['']

        #self.fields['requeue'].widget


class GTQueueEntryInline(admin.StackedInline):
    model = models.GTQueueEntry
    form = GTQueueEntryInlineForm

    raw_id_fields = ['tag', 'record']
    autocomplete_lookup_fields = {
            'fk': ['tag', 'record'],
           # 'm2m': ['related_m2m'],
    }
    readonly_fields = ('id','tag', 'record', 'submitter',  'administration_time','administrator')
   # exclude = [] #todo include sometimes
    extra = 1




#    def get_readonly_fields(self, request, obj=None):
#        print "tst", obj
#        if obj is None:
#            return ('administration_time','administrator',)
#        else:
##            return ()
#            return


#
#    def __init__(self, *args, **kwargs):
#        super(GTQueueEntryInline, self).__init__(*args, **kwargs)
#        self.fields['requeue'] =  django.forms.URLField(label='Requeue', initial="http://google.com", required=False)


    def queryset(self, request):



        """

"""
        qs = super(GTQueueEntryInline, self).queryset(request).select_related('tag','record','submitter','administrator' )
#        query = '''SELECT a.*, b.tc
#        FROM   "GlobalTagQueues_gtqueueentry" As [a]
#         INNER
#          JOIN
#          (
#
#        SELECT "GlobalTagQueues_gtqueueentry"."id",
#          "GlobalTagQueues_gtqueueentry"."tag_id",
#          "GlobalTagQueues_gtqueueentry"."record_id",
#          "GlobalTagQueues_gtqueueentry"."label",
#          "GlobalTagQueues_gtqueueentry"."status",
#          count("GlobalTagQueues_gtqueueentry"."tag_id") as tc
#        FROM "GlobalTagQueues_gtqueueentry"
#        WHERE "GlobalTagQueues_gtqueueentry"."queue_id" = '1'
#
#        GROUP BY
#          "GlobalTagQueues_gtqueueentry"."record_id",
#          "GlobalTagQueues_gtqueueentry"."label",
#          "GlobalTagQueues_gtqueueentry"."tag_id"
#        HAVING Count(*) > 0
#
#        ) As [b]
#            ON a.record_id = b.record_id
#           AND a.tag_id = b.tag_id
#           AND a.label = b.label
#        WHERE a."queue_id" = '1' '''
        #rz = models.GTQueueEntry.objects.raw(query)
        #return rz
#        s = ''' SELECT "GlobalTagQueues_gtqueueentry"."id",
#                  "GlobalTagQueues_gtqueueentry"."tag_id",
#                  "GlobalTagQueues_gtqueueentry"."record_id",
#                  "GlobalTagQueues_gtqueueentry"."label",
#                  "GlobalTagQueues_gtqueueentry"."status",
#                  count("GlobalTagQueues_gtqueueentry"."tag_id") as tc '''
#        qs = qs.extra(select={'avg_rating':s})
#        qs.annotate(stc=Count('queue', 'tag','record','label'))
#        GTQueueEntry.objects.filter(queue=self.queue, tag=self.tag,record=self.record, label=self.label ).count() <=1

        tb_name = models.GTQueueEntry()._meta.db_table
        query = '''
        	SELECT COUNT(*)
        	FROM {tb_name}  gtqe
        	WHERE
        	    ({tb_name}.queue_id = gtqe.queue_id AND
        	     {tb_name}.record_id = gtqe.record_id AND
        	     {tb_name}.tag_id = gtqe.tag_id AND
        	     {tb_name}.label = gtqe.label)
        '''.format(tb_name=tb_name)
        qs = qs.extra(select={'tc':query})






        if request.GET.__contains__("all"):
            return qs
        return qs.filter(~Q(status='O')) #TODO document

class MultipleFormBase(BaseModelForm):
    """

    """

    def __init__(self, data, files):
        super(MultipleFormBase, self).__init__()
        self.forms = [form_class(data, files, prefix) for form_class, prefix in
                      self.form_class.iteritems()]
    def as_table(self):
        """

        """
        return "\n".join([form.as_table() for form in self.forms])

    def save(self, commit=True):
        """

        """
        return tuple(form.save(commit) for form in self.forms)

    def is_valid(self):
        """

        """
        return all(form.is_valid for form in self.forms)

#def multipleform_factory(form_classes, form_order=None):
#    if form_order:
#        form_classes = SortedDict([(prefix, form_classes[prefix]) for prefix in form_order])
#    else:
#        form_classes = SortedDict(form_classes)
#    return type('MultipleForm', (MultipleFormBase,),{'form_classes':form_classes})


class GTQueueAdminForm(django.forms.ModelForm):
    class Meta:
        model = models.GTQueue

    def clean_expected_gt_name(self):
        expected_gt_name = self.cleaned_data['expected_gt_name']
        if expected_gt_name == '':
            expected_gt_name = None
        return expected_gt_name


#DoubleForm = multipleform_factory({'af':GTQueueAdminForm,'wlf':WaitingListForm}, ['af','wlf'])

class GTQueueAdmin(admin.ModelAdmin):
    #TODO add queue creator (user)
    #TODO CREATE GLOBAL TAG
    inlines = [GTQueueEntryInline]
    class Meta:
        model = GTQueueAdminForm

    #form = #type(MultipleForm)# {'k':v, 'k':v}
#    form = DoubleForm

    raw_id_fields = ('last_gt','release_from', 'release_to','gt_account','gt_type_category')
    autocomplete_lookup_fields = {
            'fk': ['last_gt', 'release_from', 'release_to','gt_account','gt_type_category'],
           # 'm2m': ['related_m2m'],
    }
    list_display = ('name', 'num_pending','last_gt','expected_gt_name')

    def num_pending(self, obj):
        """

        """
        return obj.num_pending
    num_pending.admin_order_field='num_pending'

#
#    def gtwaitinglist_name(selfself, obj):
#        o = obj.gtwaitinglist_set.all()
#        if len(o) > 0:
#            return o[0].expected_gt_name
#        return ""

    def queryset(self, request):
        """

        """
        qs = super(GTQueueAdmin, self).queryset(request)
        tb_name = models.GTQueueEntry()._meta.db_table
        qs = qs.extra(select={'num_pending': 'SELECT COUNT(*) FROM {tb_name} WHERE ({tb_name}.status =\'P\') and ({tb_name}.queue_id = globaltagcollector_gtqueue.id)'.format(tb_name=tb_name)} )
        return qs


    def get_readonly_fields(self, request, obj=None):
        """

        """
        if obj is None:
            return ()
        else:
            return 'last_gt','gt_account','gt_type_category',

    def save_model(self, request, obj, form, change):
        """

        """
        if not change:
            #obj.save()
            rez = super(GTQueueAdmin, self).save_model(request, obj, form, change)
            print request.user
            print request.user.id
            QueueObjectCreator().create_queue_entries_from_gt(obj, request.user)
            return rez
        else:
            return super(GTQueueAdmin, self).save_model(request, obj, form, change)

    def change_view(self, request, object_id, extra_context=None):
        #waiting_list_form =
        """

        """
        #waiting_list_object = None
        waiting_list_form = None
#        print "wlo", dir(object_id)
#        wlo_list = models.GTWaitingList.objects.filter(queue=object_id)[:1]
#        if len(wlo_list) != 0:
#            waiting_list_object = wlo_list[0]
#            waiting_list_form = WaitingListForm(instance=waiting_list_object)
#            print waiting_list_form

       # multipleform_cactory()
        my_context = {
            'osm_data': '123',
            'waiting_list_form': waiting_list_form
        }
        return super(GTQueueAdmin, self).change_view(request, object_id,
            extra_context=my_context)














#from django.forms.formsets import BaseFormSet, BaseFormSet, formset_factory
#from django import forms
#from django.forms import ModelForm
#
#
#class GTQueueEntryForm(ModelForm):
#    #todo prohibid ID fields
#    class Meta:
#        model = models.GTQueueEntry
#        exclude = ('queue', 'status')
#
#    class Media:
#        js =  ('js/jquery.js',)
#
#
#
#
#    def __init__(self, *args, **kwargs):
#        super(GTQueueEntryForm, self).__init__(*args, **kwargs)
#        self.fields.keyOrder = ['account_type', 'account',  'tag', 'record', 'label', 'comment',  'queue_choices']
#  #      self.fields["tag"].queryset = models.Tag.objects.none()
#  #      self.fields["record"].queryset = models.Record.objects.none()
#
#    #def __init__(self):
#    #    super(ModelForm, self).__init__(*args, **kw)
#   #     self.fields.keyOrder = ['auto_id','tag', 'record', 'label', 'comment', 'account_type', 'account', 'queue_choices']
#
#    account_type = forms.ModelChoiceField(queryset=Accounts.models.AccountType.objects.all())
#    account = forms.ModelChoiceField(queryset=Accounts.models.Account.objects.all())
#    queue_choices = forms.ModelMultipleChoiceField(queryset=models.GTQueue.objects.filter(is_open=True),
#                                           widget=forms.CheckboxSelectMultiple)
#
#    def clean(self):
#        super(GTQueueEntryForm, self).clean()
#        cleaned_data = self.cleaned_data
#
#        account_type = cleaned_data.get('account_type', None)
#        account = cleaned_data.get('account', None)
#        tag = cleaned_data.get('tag', None)
#        record = cleaned_data.get('record', None)
#
#        if (account_type is not None) and (account is not None) and (account.account_type != account_type):
#            self._errors['account'] = self.error_class(["Account must belong to account selected type"])
#            del cleaned_data['account']
#
#        if ((account is not None) and (tag is not None) and (tag.account != account)):
#            self._errors['tag'] = self.error_class(["Tag must belong to account"])
#            del cleaned_data['tag']
#
#        if ((tag is not None) and (record is not None) and (tag.object_r != record.object_r)):
#            self._errors['record'] = self.error_class(["Record mus belong to the tag"])
#            del cleaned_data['record']
#
#        return cleaned_data







class GTQueueEntryAdmin(admin.ModelAdmin):
    list_display = ['queue', 'tag', 'record', 'label', 'comment', 'status','safe_to_change','submitter', 'administrator', 'submitting_time', 'administration_time']
    #readonly_fields = ['queue', 'tag', 'record', 'label', 'submitting_time','administration_time','administrator','submitter']
 #   list_editable = ['status']
    list_filter = ['status', 'submitting_time', 'administration_time'] #safe to change
    search_fields = ('queue__name', 'tag__name', 'record__name','label')
    list_per_page = 25
    exclude = ('administration_time','administrator')

    raw_id_fields = ('queue', 'tag', 'record', )
    autocomplete_lookup_fields = {
            'fk': ('queue', 'tag', 'record',    )
           # 'm2m': ['related_m2m'],
    }

    def safe_to_change(self, obj):
        """

        """
        return obj.safe_to_change() #todo speedup

    def save_model(self, request, obj, form, change):
        """

        """
        obj.administrator = request.user
        obj.administration_time = datetime.datetime.now()
        obj.save()

#
#    def add_view(self, request, form_url='', extra_context=None):
#        form = super(GTQueueEntryAdmin, self).add_view(self, request, form_url, extra_context)
#        if 1==2:
#            print dir(form)
#        return form



#    def has_add_permission(self, request):
#        return False
    def get_readonly_fields(self, request, obj=None):
        """

        """
        if obj is None:
            return ()#('administration_time','administrator')
        else:
            return ['queue', 'tag', 'record', 'label', 'submitting_time','administration_time','administrator','submitter']

    def has_delete_permission(self, request, obj=None):
        """

        """
        return False

    def get_form(self, request, obj=None):
        """

        """
        form = super(GTQueueEntryAdmin, self).get_form(request, obj)
        if obj is not None:


            print obj.status
            if  obj.status == 'O':
                form.base_fields['status'].choices =( ('O', 'Original'),)
                print "ok"
            if ( obj.status == 'P') or ( obj.status == 'R'):
                form.base_fields['status'].choices =( ('P', 'Pending'), ('A', 'Approved'),('R', 'Rejected'),)
            if  obj.status == 'A':
                form.base_fields['status'].choices =( ('A', 'Approved'),)
            if  obj.status == 'I':
                form.base_fields['status'].choices =( ('I', 'Ignored'),)
            print form.base_fields['status'].choices
        else:
            if (request.method == 'GET') and (request.GET.__contains__('requeue_id')):
                id = request.GET['requeue_id']
                try:
                    id = int(id)
                except ValueError:
                    raise Http404
                queue_entry = get_object_or_404(models.GTQueueEntry, pk=id)

                    #form.base_fields['queue'].queryset = models.GTQueue.objects.all()
                #form.base_fields['queue'].initial = queue_entry.queue
                form.base_fields['tag'].initial =  queue_entry.tag
                form.base_fields['record'].initial =  queue_entry.record
                form.base_fields['label'].initial =  queue_entry.label
                form.base_fields['comment'].initial =  queue_entry.comment
                form.base_fields['status'].initial =  queue_entry.status
                form.base_fields['submitter'].initial =  queue_entry.submitter
    #            print request.user.__class__
    #            print form.base_fields.keys()
    #            form.base_fields['administrator'].initial =  request.user #read only and cannot be set



        return form

        #someday add not only template security but and module level security

class GTWaitingListAdmin(admin.ModelAdmin):
    list_display = ['queue', 'expected_gt_name', 'export_link']

    def export_link(self, obj): #TODO icon reqired expected_gt_name
        """

        """
        tmp = urlencode({'x':obj.expected_gt_name})
        url = tmp[2:]
        return "<a href='/gt_conf_export/%s'> %s</a>" % (url, html.escape(obj.expected_gt_name))
    export_link.allow_tags = True
    export_link.admin_order_field = 'expected_gt_name'
    export_link.short_description = 'Configuration file link'
    pass
#def formfield_for_dbfield(self, db_field, **kwargs):
        #user = kwargs['request'].user
     #   if db_field.name == "queue":
            #kwargs['initial'] = None# user.default_company
      #      qs = models.GTQueue.objects.all()[:2]
       #     kwargs['que_ue'] = qs
            #return forms.ModelChoiceField(queryset=qs, **kwargs)
        #return super(GTWaitingListAdmin, self).formfield_for_dbfield(db_field, **kwargs)


admin.site.register(models.GTAccount, GTAccountAdmin)
admin.site.register(models.GTQueue, GTQueueAdmin)
admin.site.register(models.GTQueueEntry, GTQueueEntryAdmin)
admin.site.register(models.GTType, GTTypeAdmin)
admin.site.register(models.GTTypeCategory, GTTypeCategoryAdmin)

#admin.site.register(models.GTWaitingList,GTWaitingListAdmin)
#---------------------------------------------------------------------------


class GlobalTagAdmin(DetailsViewMixin, admin.ModelAdmin):
   # date_hierarchy = 'external_finding_timestamp'
    list_filter = ['external_finding_timestamp',]
    list_display = ('link_to_details', 'internal_creation_timestamp', 'external_finding_timestamp', 'creator')
    details_url_name = "GlobalTags_globaltag_details"
    details_link_text_resource = "name"
    details_template = 'admin/globaltagcollector/globaltag/detail_view.html'
    list_display_links = []
    details_short_description = "Name"
    details_admin_order_field = "name"
    search_fields = ['name',]

    def has_delete_permission(self, request, obj=None):
        """

        """
        return False

    def has_add_permission(self, request):
        """

        """
        return False

    def has_change_permission(self, request, obj=None):
        """

        """
        return obj is None


admin.site.register(models.GlobalTag, GlobalTagAdmin)

#---------------------------
class AccountTypeAdmin(admin.ModelAdmin):

    list_display = ('title', 'visible_for_users', 'connection_string',)
    fields = ('title', 'visible_for_users',  'connection_string',)
    list_filter = ('visible_for_users', )
    search_fields = ('title',  'connection_string',)

    def has_delete_permission(self, request, obj=None):
        """

        """
        return (obj is None) or (obj.account_set.count() ==  0)

admin.site.register(models.AccountType, AccountTypeAdmin)


class AccountAdmin(admin.ModelAdmin):
 #   fields = ('account_type', 'name', )
    list_display = ( 'link_to_account_view','link_to_account_type')
    list_filter = ('account_type',)
    search_fields = ('name',)

    def queryset(self, request):
        """

        """
        return super(AccountAdmin, self).queryset(request).select_related().select_related('account_type')

    def link_to_account_type(self, obj):
        """

        """
        url = reverse('admin:GlobalTagCollector_accounttype_change', args=(obj.account_type.pk,))
        return "<a href='%s'>%s</a>" % (url, html.escape(obj.account_type))
    link_to_account_type.allow_tags = True
    link_to_account_type.admin_order_field = 'account_type__name'
    link_to_account_type.short_description = 'Account type'

    #It is allowed only to read data. Adding/Editing and modifying is not permitted
    def has_add_permission(self, request):
        """

        """
        return False

    def has_delete_permission(self, request, obj=None):
        """

        """
        return False

    def has_change_permission(self, request, obj=None):
        """

        """
        return obj is None

    def get_urls(self):
        """

        """
        urls = super(AccountAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^view/(?P<id>\d+)/$', self.admin_site.admin_view(self.details), name='GlobalTagCollector_account_details')
        )
        return my_urls + urls

    def link_to_account_view(self, obj):
        """

        """
        url = reverse('admin:GlobalTagCollector_account_details', args=(obj.pk,) )
        return "<a href='%s'>%s</a>" % (url, html.escape(obj.name))
    link_to_account_view.allow_tags = True
    link_to_account_view.admin_order_field = 'private_name'
    link_to_account_view.short_description = 'Name'

    #TODO when to use staff member required
    def details(self,request, id):

        """

"""
        account = get_object_or_404(models. Account, id=id)
        opts = models.Account._meta
        app_label = opts.app_label
        config_detail_view_template = 'admin/globaltagcollector/account/detail_view.html'
        cxt = {
           'resource_url' : settings.SERVICE_TAGS_FOR_ACCOUNT + account.name,
           'account' : account,
           'opts' : opts,
           'app_label' : app_label,
        }
        return render_to_response(config_detail_view_template , cxt, context_instance=RequestContext(request))

admin.site.register(models.Account, AccountAdmin)


class TagAdmin(DetailsViewMixin, admin.ModelAdmin):
    list_display = ('link_to_details',  'object_r', 'record_count', 'link_to_account', 'link_to_account_type') #first was name
#   fields = ( 'account', 'name', 'object_r')
    list_filter = ('account__account_type',)
    search_fields = ['name','object_r__name', 'account__name']


    details_url_name = "GlobalTagCollector_tag_details"
    details_link_text_resource = "name"
    details_template = 'admin/globaltagcollector/tag/detail_view.html'
    list_display_links = []
#   details_short_description = "Name"
#   details_admin_order_field = "name"

    def link_to_details(self, obj): #FIX and remove
        """

        """
        url = reverse('admin:'+self.details_url_name, args=(obj.id,))
        resource = getattr(obj, self.details_link_text_resource, None)
        if (resource is not None) and callable(resource):
            url_text = resource()
        return "<a href='%s'>%s</a>" % (url, html.escape(obj.name))
    link_to_details.allow_tags = True

    def queryset(self, request):
        qs = super(TagAdmin, self).queryset(request)
        qs = qs.annotate(obj_r_c=Count('object_r__record'))
        return qs

    def link_to_account(self, obj):
        url = reverse('admin:GlobalTagCollector_account_details', args=(obj.account.pk,))
        return "<a href='%s'>%s</a>" % (url, html.escape(obj.account.name))
    link_to_account.allow_tags = True
    link_to_account.admin_order_field = 'account__name'
    link_to_account.short_description = 'Account'

    def record_count(self, obj):
       # print dir(obj)
       # return obj.object_r__record__count #TODO ordering and filtering by count
        return obj.obj_r_c
       # print obj.records()
       # return obj.records().count()


    def link_to_account_type(self, obj):
        url = reverse('admin:GlobalTagCollector_accounttype_change', args=(obj.account.account_type.pk,))
        return "<a href='%s'>%s</a>" % (url, html.escape(obj.account.account_type))
    link_to_account_type.allow_tags = True
    link_to_account_type.admin_order_field = 'account__account_type__title'
    link_to_account_type.short_description = 'Account type'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None

admin.site.register(models.Tag, TagAdmin)
#admin.site.disable_action('delete_selected')
#
#class OldAccountTypeAdmin(admin.ModelAdmin):
#
#    list_display = ('name', 'enabled', 'accounts_url', 'tags_url', )
#    fields = ('name', 'enabled', 'accounts_url', 'tags_url', )
#    list_filter = ('enabled', )
#    search_fields = ('name', 'accounts_url', 'tags_url', )
#    list_filter = ('name',)
#
#    def has_delete_permission(self, request, obj=None):
#        return (obj is None) or (obj.account_set.count() ==  0)
#
#admin.site.register(models.OldAccountType, OldAccountTypeAdmin)
#
#
#class OldAccountAdmin(admin.ModelAdmin):
#
#
#    fields = ('account_type', 'private_name', 'public_name')##??
#    list_display = ('link_to_account_type', 'link_to_account_view', 'public_name')
#   # list_display_links = ()
#  #  readonly_fields = ('account_type', 'private_name', 'public_name')
#    list_filter = ('account_type',)
#    search_fields = ('public_name','private_name',)
#
#    def queryset(self, request): #TODO it seems it possible to use configs for this
#        return super(OldAccountAdmin, self).queryset(request).select_related()
#
#
#    def link_to_account_type(self, obj):
#        url = reverse('admin:Accounts_accounttype_change', args=(obj.account_type.pk,))
#        return "<a href='%s'>%s</a>" % (url, html.escape(obj.account_type))
#    link_to_account_type.allow_tags = True
#    link_to_account_type.admin_order_field = 'account_type__name'
#    link_to_account_type.short_description = 'Account type'
#
#
#
#
#    #It is allowed only to read data. Adding/Editing and modifying is not permitted
#    def has_add_permission(self, request):
#        return False
#
#    def has_delete_permission(self, request, obj=None):
#        return False
#
#    def has_change_permission(self, request, obj=None):
#        return obj is None
#
#    def get_urls(self):
#        urls = super(OldAccountAdmin, self).get_urls()
#        my_urls = patterns('',
#            url(r'^view/(?P<id>\d+)/$', self.admin_site.admin_view(self.details), name='Accounts_account_details')
#        )
#        return my_urls + urls
#
#    def link_to_account_view(self, obj):
#        url = reverse('admin:Accounts_account_details', args=(obj.pk,) )
#        return "<a href='%s'>%s</a>" % (url, html.escape(obj.private_name))
#    link_to_account_view.allow_tags = True
#    link_to_account_view.admin_order_field = 'private_name'
#    link_to_account_view.short_description = 'Private name'
#
#    #TODO when to use staff member required
#    def details(self,request, id):
#        account = get_object_or_404(models.OldAccount, id=id)
#        opts = models.OldAccount._meta
#        app_label = opts.app_label
#        config_detail_view_template = 'admin/accounts/account/detail_view.html'
#        cxt = {
#           'account' : account,
#           'opts' : opts,
#           'app_label' : app_label,
#        }
#        return render_to_response(config_detail_view_template , cxt, context_instance=RequestContext(request))
#
#admin.site.register(models.OldAccount, OldAccountAdmin)
##FIX URL's validation
#
#
#
#
#class TagAdmin(DetailsViewMixin, admin.ModelAdmin):
#    list_display = ('link_to_details',  'object_r', 'record_count', 'link_to_account', 'link_to_account_type') #first was name
# #   fields = ( 'account', 'name', 'object_r')
#    list_filter = ('account__account_type',)
#    search_fields = ['name','object_r__name', 'account__private_name']
#
#
#    details_url_name = "Tags_tag_details"
#    details_link_text_resource = "name"
#    details_template = 'admin/tags/tag/detail_view.html'
#    list_display_links = []
# #   details_short_description = "Name"
# #   details_admin_order_field = "name"
#
##    def link_to_details(self, obj): #FIX and remove
##        url = reverse('admin:'+self.details_url_name, args=(obj.id,))
##        resource = getattr(obj, self.details_link_text_resource, None)
##        if (resource is not None) and callable(resource):
##            url_text = resource()
##        return "<a href='%s'>%s</a>" % (url, html.escape(obj.name))
##    link_to_details.allow_tags = True
#
#    def queryset(self, request):
#        qs = super(TagAdmin, self).queryset(request)
#        qs = qs.annotate(Count('object_r__record'))
#        return qs
#
#    def link_to_account(self, obj):
#        url = reverse('admin:Accounts_account_details', args=(obj.account.pk,))
#        return "<a href='%s'>%s</a>" % (url, html.escape(obj.account.private_name))
#    link_to_account.allow_tags = True
#    link_to_account.admin_order_field = 'account__private_name'
#    link_to_account.short_description = 'Account'
#
#    def record_count(self, obj):
#       # print dir(obj)
#        return obj.object_r__record__count #TODO ordering and filtering by count
#
#
#    def link_to_account_type(self, obj):
#        url = reverse('admin:Accounts_accounttype_change', args=(obj.account.account_type.pk,))
#        return "<a href='%s'>%s</a>" % (url, html.escape(obj.account.account_type))
#    link_to_account_type.allow_tags = True
#    link_to_account_type.admin_order_field = 'account__account_type__name'
#    link_to_account_type.short_description = 'Account type'
#
#    def has_delete_permission(self, request, obj=None):
#        return False
#
#    def has_add_permission(self, request):
#        return False
#
#    def has_change_permission(self, request, obj=None):
#        return obj is None
#
class RecordAdmin(DetailsViewMixin, admin.ModelAdmin):
    list_display = ('link_to_details', 'object_r', 'tag_count')
    search_fields = ('name', 'object_r__name')

    details_url_name = "GlobalTagCollector_record_details"
    details_link_text_resource = "name"
    details_template = 'admin/globaltagcollector/record/detail_view.html'
    list_display_links = []
#   details_short_description = "Name"
#   details_admin_order_field = "name"


    def queryset(self, request):
        qs = super(RecordAdmin, self).queryset(request)
        qs = qs.annotate(Count('object_r__tag'))
        return qs

    def tag_count(self, obj):
        return obj.object_r__tag__count #TODO ordering and filtering by count

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None

#admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Record, RecordAdmin)

#
#
#
class HardwareArchitectureAdmin(DetailsViewMixin, admin.ModelAdmin):
    details_url_name = "GlobalTagCollector_HardwareArchitecture_details"
    details_link_text_resource = "name"
    details_template = 'admin/globaltagcollector/hardwarearchitecture/detail_view.html'
#   details_short_description = "Name"
#   details_admin_order_field = "name"

    list_display = ('link_to_details', 'link_to_delete_hardware_architecture',)
    list_display_links = []

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return  obj is None

    def link_to_delete_hardware_architecture(self, obj): #TODO icon reqired
        url = reverse('admin:GlobalTagCollector_hardwarearchitecture_delete', args=(obj.id,))
        return "<a href='%s'>[X] Delete %s</a>" % (url, html.escape(obj.name))
    link_to_delete_hardware_architecture.allow_tags = True
    link_to_delete_hardware_architecture.admin_order_field = 'id'
    link_to_delete_hardware_architecture.short_description = 'Delete'


class SoftwareReleaseAdmin(admin.ModelAdmin):
    readonly_fields = ['name', 'hardware_architecture']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(models.HardwareArchitecture, HardwareArchitectureAdmin)
admin.site.register(models.SoftwareRelease, SoftwareReleaseAdmin)




class AccountandTypeChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s, %s "  % (obj.name, obj.account_type.title)
