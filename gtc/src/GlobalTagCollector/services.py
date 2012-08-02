from django.http import HttpResponse
import json
import models

def list_queues(request):
    rez = models.GTQueue.objects.values(
        'id',
        'name',
        'is_open',
        'description',
        'expected_gt_name',
        'last_gt_id__name',
        'release_from__name',
        'release_to__name',
        'gt_account__name',
        'gt_type_category__name',
    ).select_related()




    return HttpResponse(json.dumps(list(rez)), mimetype="application/json")
