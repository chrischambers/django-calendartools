from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/$', views.today_agenda, name='agenda'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/$',
        views.YearAgenda.as_view(), name='year-agenda'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/triple/$',
        views.TriMonthAgenda.as_view(), name='tri-month-agenda'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/$',
        views.MonthAgenda.as_view(), name='month-agenda'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<week>[1-5]?\d)/$',
        views.WeekAgenda.as_view(), name='week-agenda'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$',
        views.DayAgenda.as_view(), name='day-agenda'),
)

