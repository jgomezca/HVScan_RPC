from django.conf.urls import patterns, include, url


from django.contrib import admin
from django.views.generic.base import TemplateView

admin.autodiscover()



#from tastypie.api import Api
#from GlobalTagCollector.api import AccountTypesResource, QueueResource, AccountsResource, TagsResource
from GlobalTagCollector.admin2 import gt_queues_list, gt_queue_create, gt_queue_edit, gt_queue_entries, gt_queue_entry_status_change, dashboard, gt_info
from GlobalTagCollector.views import gt_conf_export, new_request, list_view, details_view, json_account_types, json_accounts, json_tags, json_records, json_queues_for_record, login

from django.contrib.staticfiles.urls import staticfiles_urlpatterns


#v1_api = Api(api_name='v1')
#v1_api.register(AccountTypesResource())
#v1_api.register(QueueResource())
#v1_api.register(AccountsResource())
#v1_api.register(TagsResource())
regular_urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gtc.views.home', name='home'),
    # url(r'^gtc/', include('gtc.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),


    url(r'^admin/', include(admin.site.urls)),
#    url(r'^api/', include(v1_api.urls)),
    url(r'^admin2/gt_queues', gt_queues_list, name="gt_queue_list"),
    url(r'^admin2/gt_queue_create', gt_queue_create, name="gt_queue_create"),
    url(r'^admin2/gt_queue_edit/(?P<queue_id>\d+)/$', gt_queue_edit, name="gt_queue_edit"),
    url(r'^admin2/gt_queue_entries/(?P<queue_id>\d+)/$', gt_queue_entries, name="gt_queue_entries"),
    url(r'^admin2/gt_queue_entry_status_change/(?P<gt_queue_entry_id>\d+)/(?P<new_status>[ARPIO])/', gt_queue_entry_status_change, name="gt_queue_entry_status_change"),
    url(r'^gt_conf_export/(?P<gt_queue_name>[a-zA-Z0-9_\-]+)$', gt_conf_export, name="gt_conf_export"),


    url(r'^new-request$', new_request, name="new_request"),
    url(r'^list_view$', list_view, name="list_view"),
    url(r'^details_view/(?P<id>\d+)$', details_view, name="details_view"),
    url(r'^submit-tag-success/$',
        name="submit_record_success",
        view=TemplateView.as_view(template_name="GlobalTagCollector/submit-record-success.html"),
    ),


    url(r'^json/account_types/$', json_account_types,),
    url(r'^json/accounts/$',json_accounts,),
    url(r'^json/tags/$',json_tags,),
    url(r'^json/records/$',json_records,),
    url(r'^json/queues/$', json_queues_for_record,),
    url(r'^accounts/login/', login,),
    url(r'^admin2/$', dashboard,),
    url(r'^admin2/gt_info/(?P<gt_name>[a-zA-Z0-9_\-]+)$', gt_info, name='gt_info'),





)
#regular_urlpatterns += staticfiles_urlpatterns()

urlpatterns = patterns('',

    (r'^gtc/', include(regular_urlpatterns)),
    (r'^gtc/', include(staticfiles_urlpatterns()))
)