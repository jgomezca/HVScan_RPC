import datetime
from django.db import models




class ImportedGTByDate(models.Manager):

    def _date(self, from_date=None, till_date=None):
        queryset = self.all()
        #print queryset
        if from_date is not None:
            queryset = queryset.filter(external_finding_timestamp__gte=from_date)
            #print queryset
        if till_date is not None:
            queryset = queryset.filter(external_finding_timestamp__lt=till_date)
            #print queryset
        return queryset.order_by('external_finding_timestamp')

    def today(self):
        today = datetime.date.today()
        return self._date(from_date=today)

    def yesterday(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        return self._date(from_date=yesterday, till_date=today)

    def last_7_days(self):
        today = datetime.date.today()
        ago_7_days = today - datetime.timedelta(days=7)
        return self._date(from_date=ago_7_days, till_date=today)
