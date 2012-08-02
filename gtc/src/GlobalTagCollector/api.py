#from django.db.models.aggregates import Count
#from tastypie import fields
#from tastypie.resources import ModelResource
#from tastypie.constants import ALL, ALL_WITH_RELATIONS
#from GlobalTagCollector.models import GTQueue, AccountType, Account, Tag
#
#
#class QueueResource(ModelResource):
#    class Meta:
#        queryset = GTQueue.objects.all()
#        resource_name = 'queue'
#        allowed_methods = ['get']
#        limit = 0
#
#
#class AccountTypesResource(ModelResource):
#    class Meta:
#        queryset = AccountType.objects.filter(visible_for_users=True).order_by('title')
#        resource_name = 'account_types'
#        allowed_methods = ['get', 'list']
#        fields = ['id', 'title']
#        limit = 0
#
#
#class AccountsResource(ModelResource):
#    class Meta:
#        queryset = Account.objects.filter(account_type__visible_for_users=True).annotate(num_tags=Count('tag')).filter(num_tags__gt = 0).order_by('name')
#        allowed_methods = ['get', 'list']
#        resource_name = 'accounts'
#        fields = ['id', 'name']
#        limit = 0
##        filtering = {
##            'account_type': ALL_WITH_RELATIONS,
##        }
#
#
#class TagsResource(ModelResource):
#
#    account = fields.ForeignKey(AccountsResource, 'account')
#
#    class Meta:
#        queryset = Tag.objects.filter().order_by('name')
#        allowed_methods = ['get', 'list']
#        resource_name = 'tags'
#        fields = ['id', 'name', 'account']
#        limit = 0
#        filtering = {
#            'account': ALL,
#            'name': ALL,
#        }
#
#
##def json_tags(request):
##    objects = Tag.objects.filter(account=int_or_zero(request.GET.get('parent', None))).order_by('name')
##    obj_dics = [{'id': obj.id, 'name':obj.name} for obj in objects]
##    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")
#
#
#
#class RecordsResource(ModelResource):
#    class Meta:
#        pass
##def json_records(request): #TODO try except
##    tag = Tag.objects.get(pk=int_or_zero(request.GET.get('parent', None)))
##    objects = Record.objects.filter(object_r__tag=tag).all()
##    obj_dics = [{'id': obj.id, 'name':obj.name} for obj in objects]
##    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")
##
#
##def json_queues_for_record(request): #TODO try except
##    """
##
##    """
##    record = Record.objects.get(pk=int_or_zero(request.GET.get('parent', None)))
##    record_releases = list(record.software_release.all().order_by('internal_version'))
##    lowest_internal_version = record_releases[0].internal_version
##    higest_internal_version = record_releases[-1].internal_version
##    #TODO hardware ach , open.
##    queue_list = GTQueue.objects.filter(release_from__lte=higest_internal_version).filter(Q(release_to__gte=lowest_internal_version) | Q(release_to=None)).order_by('name')
##    obj_dics = [{'id': obj.id, 'name':obj.name, 'descr':obj.description } for obj in queue_list] #obj.description
##    return HttpResponse(json.dumps(obj_dics), mimetype="application/json")
