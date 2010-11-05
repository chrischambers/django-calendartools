from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^$', views.today_view, name='calendar'),
    url(r'^(?P<year>\d{4})/$',
        views.year_view, name='year-calendar'),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/$',
        views.month_view, name='month-calendar'),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$',
        views.day_view, name='day-calendar'),

    (r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/(?P<slug>[-_0-9A-Za-z]*)/(?P<pk>\d+)/$',
        views.occurrence_detail_redirect),
)
