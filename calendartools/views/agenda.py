import time
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from calendartools.models import Calendar, Occurrence
from calendartools.periods import Year, Month, Week, Day

def year_agenda(request, slug, year, *args, **kwargs):
    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year = int(year)

    occurrences = Occurrence.objects.visible().select_related('event').filter(
        calendar=calendar,
        start__year=year).order_by('start')

    period = request.GET.get('period')
    if period in ['past', 'future', 'today']:
        if period == 'past':
            occurrences = occurrences.filter(start__lt=datetime.now())
        elif period == 'future':
            occurrences = occurrences.filter(start__gte=datetime.now())
        else:
            occurrences = occurrences.filter(
                start__year=datetime.now().year,
                start__month=datetime.now().month,
                start__day=datetime.now().day
            )

    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'year': Year(date(year, 1, 1), occurrences=occurrences),
        'filters': {'period': period}
    }
    return render_to_response("calendar/year_agenda.html", data,
                            context_instance=RequestContext(request))

def month_agenda(request, slug, year, month, month_format='%b', *args,
                 **kwargs):

    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year = int(year)

    try:
        tt = time.strptime("%s-%s" % (year, month), '%s-%s' % ('%Y', month_format))
        d = date(*tt[:3])
    except ValueError:
        raise Http404

    occurrences = Occurrence.objects.visible().select_related('event').filter(
        calendar=calendar,
        start__year=d.year, start__month=d.month,
    ).order_by('start')

    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'month': Month(d, occurrences=occurrences)
    }
    return render_to_response("calendar/month_agenda.html", data,
                            context_instance=RequestContext(request))


def week_agenda(request, slug, year, week, *args, **kwargs):
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
    return render_to_response("calendar/week_agenda.html", data,
                            context_instance=RequestContext(request))

def day_agenda(request, slug, year, month, day, month_format='%b', *args,
               **kwargs):

    calendar = get_object_or_404(Calendar.objects.visible(request.user), slug=slug)
    year, day = int(year), int(day)

    try:
        tt = time.strptime("%s-%s-%s" % (year, month, day), '%s-%s-%s' % (
            '%Y', month_format, '%d'))
        d = date(*tt[:3])
    except ValueError:
        raise Http404

    occurrences = Occurrence.objects.visible().select_related('event').filter(
        calendar=calendar,
        start__year=d.year, start__month=d.month, start__day=d.day
    ).order_by('start')

    data = {
        'calendar': calendar,
        'occurrences': occurrences,
        'day': Day(d, occurrences=occurrences)
    }
    return render_to_response("calendar/day_agenda.html", data,
                            context_instance=RequestContext(request))

def today_agenda(request, slug, *args, **kwargs):
    today = date.today()
    return day_agenda(request, slug, today.year, today.strftime('%b'),
                      today.day, *args, **kwargs)
