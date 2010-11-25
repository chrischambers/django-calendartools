from datetime import date

from calendartools import defaults
from calendartools.views.calendars import (
    YearView, TriMonthView, MonthView, WeekView, DayView
)


class YearAgenda(YearView):
    template_name = 'calendar/agenda/year.html'
    paginate_by = defaults.MAX_AGENDA_ITEMS_PER_PAGE


class MonthAgenda(MonthView):
    template_name = 'calendar/agenda/month.html'
    paginate_by = defaults.MAX_AGENDA_ITEMS_PER_PAGE


class TriMonthAgenda(TriMonthView):
    template_name = 'calendar/agenda/tri_month.html'
    paginate_by = defaults.MAX_AGENDA_ITEMS_PER_PAGE


class WeekAgenda(WeekView):
    template_name = 'calendar/agenda/week.html'
    paginate_by = defaults.MAX_AGENDA_ITEMS_PER_PAGE


class DayAgenda(DayView):
    template_name = 'calendar/agenda/day.html'
    paginate_by = defaults.MAX_AGENDA_ITEMS_PER_PAGE

def today_agenda(request, slug, *args, **kwargs):
    today = date.today()
    view = DayAgenda(request=request, slug=slug, year=str(today.year),
                   month=str(today.strftime('%b').lower()), day=str(today.day), **kwargs)
    return view.get(request, slug=slug, year=today.year, day=today.day)
