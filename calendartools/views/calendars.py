import time
from datetime import date

from dateutil.relativedelta import relativedelta

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import simple, list_detail

from calendartools import defaults
from calendartools.periods import Year, TripleMonth, Month, Week, Day
from calendartools.views.base import CalendarViewBase
from calendartools.views.generic.dates import (
    YearMixin, MonthMixin, WeekMixin, DayMixin
)
from django.db.models.loading import get_model

Calendar = get_model(defaults.CALENDAR_APP_LABEL, 'Calendar')
Occurrence = get_model(defaults.CALENDAR_APP_LABEL, 'Occurrence')

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


class YearView(CalendarViewBase, YearMixin):
    period_name = 'year'
    period = Year
    template_name = "calendar/calendar/year.html"

    @property
    def date(self):
        return date(int(self.get_year()), 1, 1)

    def get_context_data(self, **kwargs):
        context = super(YearView, self).get_context_data(**kwargs)
        context.update({'size': 'small'})
        return context


class MonthView(CalendarViewBase, YearMixin, MonthMixin):
    period_name = 'month'
    period = Month
    template_name = "calendar/calendar/month.html"


class TriMonthView(MonthView):
    period_name = 'tri_month'
    period = TripleMonth
    template_name = "calendar/calendar/tri_month.html"

    def get_dated_queryset(self, order='asc', **lookup):
        d = self.date
        date_field = self.get_date_field()
        qs = self.get_queryset().filter(**lookup)

        date_range = (d - relativedelta(months=1), d + relativedelta(months=2))
        filter_kwargs = {'%s__range' % date_field: date_range}
        order = '' if order == 'asc' else '-'
        return qs.filter(**filter_kwargs).order_by("%s%s" % (order, date_field))

    def get_context_data(self, **kwargs):
        context = super(TriMonthView, self).get_context_data(**kwargs)
        context.update({'size': 'small'})
        return context

    def create_period_object(self, dt, occurrences):
        return self.period(dt - relativedelta(months=1), occurrences=occurrences)


class WeekView(CalendarViewBase, YearMixin, WeekMixin):
    period_name = 'week'
    period = Week
    week_format = '%W'

    template_name = "calendar/calendar/week.html"

    @property
    def date(self):
        year = self.get_year()
        week = self.get_week()
        try:
            tt = time.strptime('%s-%s-1' % (year, week), '%Y-%U-%w')
            return date(*tt[:3])
        except ValueError:
            raise Http404

    def get_dated_queryset(self, order='asc', **lookup):
        d = self.date
        date_field = self.get_date_field()
        qs = self.get_queryset().filter(**lookup)

        date_range = (d, d + relativedelta(days=7))
        filter_kwargs = {'%s__range' % date_field: date_range}
        order = '' if order == 'asc' else '-'
        return qs.filter(**filter_kwargs).order_by("%s%s" % (order, date_field))


class DayView(CalendarViewBase, YearMixin, MonthMixin, DayMixin):
    period_name = 'day'
    period = Day
    template_name = "calendar/calendar/day.html"

def today_view(request, slug, *args, **kwargs):
    today = date.today()
    view = DayView(request=request, slug=slug, year=str(today.year),
                   month=str(today.strftime('%b').lower()), day=str(today.day), **kwargs)
    return view.get(request, slug=slug, year=today.year, day=today.day)

def occurrence_detail_redirect(request, slug, year, month, day, event_slug,
                               pk):
    return simple.redirect_to(
        request, reverse('occurrence-detail', args=(event_slug, pk)),
        permanent=True)
