from calendartools.views.generic.base import View, TemplateView, RedirectView
from calendartools.views.generic.dates import (ArchiveIndexView, YearArchiveView, MonthArchiveView,
                                     WeekArchiveView, DayArchiveView, TodayArchiveView,
                                     DateDetailView)
from calendartools.views.generic.detail import DetailView
from calendartools.views.generic.edit import CreateView, UpdateView, DeleteView
from calendartools.views.generic.list import ListView


class GenericViewError(Exception):
    """A problem in a generic view."""
    pass
