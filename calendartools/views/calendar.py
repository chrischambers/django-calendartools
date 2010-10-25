from django.views.generic import simple
from django.core.urlresolvers import reverse

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
