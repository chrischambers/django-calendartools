from datetime import date

from calendartools.views.calendars import (
    YearView, TriMonthView, MonthView, WeekView, DayView
)

class YearAgenda(YearView):
    template_name = 'calendar/agenda/year.html'


class MonthAgenda(MonthView):
    template_name = 'calendar/agenda/month.html'


class TriMonthAgenda(TriMonthView):
    template_name = 'calendar/agenda/tri_month.html'


class WeekAgenda(WeekView):
    template_name = 'calendar/agenda/week.html'


class DayAgenda(DayView):
    template_name = 'calendar/agenda/day.html'

def today_agenda(request, slug, *args, **kwargs):
    today = date.today()
    view = DayAgenda(request=request, slug=slug, year=str(today.year),
                   month=str(today.strftime('%b').lower()), day=str(today.day), **kwargs)
    return view.get(request, slug=slug, year=today.year, day=today.day)
