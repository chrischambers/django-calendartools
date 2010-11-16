from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^$', views.calendar_list, name='calendar-list'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/$', views.today_view, name='calendar-detail'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/$',
        views.year_view, name='year-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/$',
        views.month_view, name='month-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/small/$',
        views.month_view, {'small': True}, name='small-month-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/triple/$',
        views.tri_month_view, name='tri-month-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<week>[1-5]?\d)/$',
        views.week_view, name='week-calendar'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$',
        views.day_view, name='day-calendar'),

    (r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/(?P<event_slug>[-_0-9A-Za-z]*)/(?P<pk>\d+)/$',
        views.occurrence_detail_redirect),
)
