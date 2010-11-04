from django.views.generic import simple
from django.core.urlresolvers import reverse

from datetime import timedelta
class Calendar(object):

    def __init__(self, start, finish, *args, **kwargs):
        self.start  = start
        self.finish = finish
        super(Calendar, self).__init__(*args, **kwargs)

    def __iter__(self):
        current = self.start
        while current < self.finish:
            yield current
            current += timedelta(days=365)


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
