from django.views.generic import simple
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
class Calendar(object):

    def __init__(self, start, finish, *args, **kwargs):
        self.start  = start
        self.finish = finish
        super(Calendar, self).__init__(*args, **kwargs)

    def __iter__(self):
        return self.years

    @property
    def years(self):
        current = datetime(self.start.year, 1, 1)
        yield current
        while True:
            current = current.replace(year=current.year + 1)
            if current > self.finish:
                raise StopIteration
            yield current

    @property
    def months(self):
        current = datetime(self.start.year, self.start.month, 1)
        month = relativedelta(months=+1)
        yield current
        while True:
            current = current + month
            if current > self.finish:
                raise StopIteration
            yield current

    @property
    def days(self):
        current = datetime(self.start.year, self.start.month, self.start.day)
        day = timedelta(1)
        yield current
        while True:
            current = current + day
            if current > self.finish:
                raise StopIteration
            yield current

def year_view(request, *args, **kwargs):
    pass

def month_view(request, *args, **kwargs):
    pass

def day_view(request, *args, **kwargs):
    pass

def today_view(request, *args, **kwargs):
    pass

def occurrence_detail_redirect(request, year, month, day, slug, pk):
    return simple.redirect_to(
        request, reverse('occurrence-detail', args=(slug, pk)), permanent=True
    )
