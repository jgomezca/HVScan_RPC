from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        from django.contrib.sessions.models import Session
        Session.objects.all().delete()
