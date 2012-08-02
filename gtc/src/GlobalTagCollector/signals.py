import django.dispatch

GTQueueEntryAdded = django.dispatch.Signal(providing_args=["instances",])
GTQueueEntryStatusChanged = django.dispatch.Signal(providing_args=["queue_entry", "old_status",])
