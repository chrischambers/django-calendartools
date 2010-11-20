import time
from datetime import date

from dateutil.relativedelta import relativedelta

from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import simple, list_detail

from calendartools.models import Occurrence, Calendar
from calendartools.periods import Year, TripleMonth, Month, Week, Day

def calendar_list(request, *args, **kwargs):
    kwargs.update({
        'queryset': Calendar.objects.visible(request.user),
        'template_name': 'calendar/calendar_list.html'
    })
    return list_detail.object_list(request, *args, **kwargs)

def calendar_detail(request, slug, *args, **kwargs):
    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    data = {'calendar': calendar}
    return render_to_response('calendar/calendar_detail.html', data,
                            context_instance=RequestContext(request))

def year_view(request, slug, year, *args, **kwargs):
    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    data = calendar.occurrences.visible().aggregate(
        earliest_occurrence=Min('start'),
        latest_occurrence=Max('finish'),
    )
    year = int(year)

    occurrences = Occurrence.objects.visible(
                  ).select_related('event', 'calendar'
                  ).filter(calendar=calendar, start__year=year
                  ).order_by('start')
    data.update({
        'calendar': calendar,
        'occurrences': occurrences,
        'year': Year(date(year, 1, 1), occurrences=occurrences),
        'size': 'small'
    })
    return render_to_response("calendar/calendar/year.html", data,
                            context_instance=RequestContext(request))

def month_view(request, slug, year, month, month_format='%b', *args, **kwargs):
    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year = int(year)

    try:
        tt = time.strptime("%s-%s" % (year, month), '%s-%s' % ('%Y', month_format))
        d = date(*tt[:3])
    except ValueError:
        raise Http404

    occurrences = Occurrence.objects.visible(
                  ).select_related('event', 'calendar').filter(
                  calendar=calendar, start__year=d.year, start__month=d.month
                  ).order_by('start')
    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'month': Month(d, occurrences=occurrences)
    }
    small = kwargs.get('small')
    if small:
        data['small'] = True
    return render_to_response("calendar/calendar/month.html", data,
                            context_instance=RequestContext(request))

def tri_month_view(request, slug, year, month, month_format='%b', *args,
                   **kwargs):

    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year = int(year)

    try:
        tt = time.strptime("%s-%s" % (year, month), '%s-%s' % ('%Y', month_format))
        d = date(*tt[:3])
    except ValueError:
        raise Http404

    date_range = (d - relativedelta(months=1), d + relativedelta(months=2))
    occurrences = Occurrence.objects.visible(
                  ).select_related('event', 'calendar').filter(
                  calendar=calendar, start__range=date_range).order_by('start')
    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'tri_month': TripleMonth(d - relativedelta(months=1),
                                 occurrences=occurrences),
        'size': 'small',
    }
    return render_to_response("calendar/calendar/tri_month.html", data,
                            context_instance=RequestContext(request))

def week_view(request, slug, year, week, *args, **kwargs):
    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year, week = int(year), int(week)

    try:
        tt = time.strptime('%s-%s-1' % (year, week), '%Y-%U-%w')
        d = date(*tt[:3])
    except ValueError:
        raise Http404

    date_range = (d, d + relativedelta(days=7))
    occurrences = Occurrence.objects.visible(
                  ).select_related('event', 'calendar'
                  ).filter(calendar=calendar, start__range=date_range
                  ).order_by('start')

    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'week': Week(d, occurrences=occurrences)
    }
    return render_to_response("calendar/calendar/week.html", data,
                            context_instance=RequestContext(request))

def day_view(request, slug, year, month, day, month_format='%b', *args,
             **kwargs):

    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year, day = int(year), int(day)

    try:
        tt = time.strptime("%s-%s-%s" % (year, month, day), '%s-%s-%s' % (
            '%Y', month_format, '%d'))
        d = date(*tt[:3])
    except ValueError:
        raise Http404

    occurrences = Occurrence.objects.visible(
                  ).select_related('event', 'calendar'
                  ).filter(calendar=calendar, start__year=d.year,
                           start__month=d.month, start__day=d.day
                  ).order_by('start')

    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'day': Day(d, occurrences=occurrences)
    }
    return render_to_response("calendar/calendar/day.html", data,
                            context_instance=RequestContext(request))

def today_view(request, slug, *args, **kwargs):
    today = date.today()
    return day_view(request, slug, today.year, today.strftime('%b'), today.day,
                    *args, **kwargs)

def occurrence_detail_redirect(request, slug, year, month, day, event_slug,
                               pk):
    return simple.redirect_to(
        request, reverse('occurrence-detail', args=(event_slug, pk)),
        permanent=True)
