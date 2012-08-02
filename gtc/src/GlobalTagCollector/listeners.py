from django.db.models.signals import post_save
from django.dispatch import receiver
from GlobalTagCollector.models import GTQueueEntry
from GlobalTagCollector.reports import report_record_queued, report_record_status_changed
from GlobalTagCollector.signals import GTQueueEntryAdded, GTQueueEntryStatusChanged

#@receiver(post_save, sender=GTQueueEntry)
#def my_handler(sender, **kwargs):
#def report_yesterday_global_tags(): #command
#def report_last_7_days_global_tags(): #command


def queue_entry_added(sender, **kwargs): #db changes not monitored
    print "queue_entry_added", kwargs
    report_record_queued(kwargs["instances"][0]) #TODO processing only first elelemt. fix


def queue_entry_status_changed(sender, **kwargs):
    print "queue_entry_status_changed", kwargs
    report_record_status_changed(kwargs["queue_entry"],kwargs["old_status"])


GTQueueEntryAdded.connect(queue_entry_added, dispatch_uid="entry_added")
GTQueueEntryStatusChanged.connect(queue_entry_status_changed, dispatch_uid="entry_status_changed")