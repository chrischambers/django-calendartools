from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^$', views.calendar_list, name='calendar-list'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/$', views.today_view, name='calendar-detail'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/$',
        views.YearView.as_view(), name='year-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/$',
        views.MonthView.as_view(), name='month-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/small/$',
        views.MonthView.as_view(), {'small': True}, name='small-month-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/triple/$',
        views.TriMonthView.as_view(), name='tri-month-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<week>[1-5]?\d)/$',
        views.WeekView.as_view(), name='week-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$',
        views.DayView.as_view(), name='day-calendar'),
)
