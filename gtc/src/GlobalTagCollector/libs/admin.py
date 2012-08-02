try:
    from django.conf.urls import patterns, url, include #django 1.4
except:
    from django.conf.urls.defaults import  patterns, url, include #django 1.3.1
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.utils import html

class DetailsViewMixin(object):
    details_url_name = None # 'CMSSW_%s_details'%(opts.object_name)
    details_template = '' #detail_view.html
 #   details_admin_order_field = None
 #   details_short_description = "N"
    details_link_text_resource = None #takes from objet

    def get_urls(self):
        urls = super(DetailsViewMixin, self).get_urls()
        opts = self.model._meta #models.HardwareArchitecture._meta
        app_label = opts.module_name

        my_urls = patterns('',
            url(r'^details/(?P<id>\d+)/$', self.admin_site.admin_view(self.details), name=self.details_url_name)
        )
        return my_urls + urls

    def details(self, request, id):
        object = get_object_or_404(self.model, id=id)
        opts = self.model._meta
        app_label = opts.app_label
        cxt = {
            'object' : object,
            'opts' : opts,
            'app_label' : app_label,
        }
        return render_to_response(self.details_template , cxt, context_instance=RequestContext(request))

    def link_to_details(self, obj):
        url = reverse('admin:'+self.details_url_name, args=(obj.id,))
        resource = getattr(obj, self.details_link_text_resource, None)
        if (resource is not None) and callable(resource):
            url_text = resource()
        return "<a href='%s'>%s</a>" % (url, html.escape(obj.name))
    link_to_details.allow_tags = True
       # self.__class__.link_to_details.admin_order_field = self.details_admin_order_field
       # self.__class__.link_to_details.short_description = details_short_description