from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^list/$', views.calendar_list, name='calendar-list'),

    url(r'^$', views.today_view, name='calendar-detail'),
    url(r'^(?P<year>\d{4})/$', views.year_view, {'slug': ''}),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/$', views.month_view,
        {'slug': ''}),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/small/$', views.month_view,
        {'slug': '', 'small': True,}),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/triple/$', views.tri_month_view,
        {'slug': ''}),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$', views.day_view,
        {'slug': ''}),


    url(r'^(?P<slug>[-A-Za-z_]+)/$', views.today_view, name='calendar-detail'),
    url(r'^(?P<slug>[-A-Za-z_]+)/(?P<year>\d{4})/$',
        views.year_view, name='year-calendar'),
    url(r'^(?P<slug>[-A-Za-z_]+)/(?P<year>\d{4})/(?P<month>\w{3})/$',
        views.month_view, name='month-calendar'),
    url(r'^(?P<slug>[-A-Za-z_]+)/(?P<year>\d{4})/(?P<month>\w{3})/small/$',
        views.month_view, {'small': True}, name='small-month-calendar'),
    url(r'^(?P<slug>[-A-Za-z_]+)/(?P<year>\d{4})/(?P<month>\w{3})/triple/$',
        views.tri_month_view, name='tri-month-calendar'),
    url(r'^(?P<slug>[-A-Za-z_]+)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$',
        views.day_view, name='day-calendar'),

    (r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/(?P<event_slug>[-_0-9A-Za-z]*)/(?P<pk>\d+)/$',
        views.occurrence_detail_redirect),
    (r'^(?P<slug>[-A-Za-z_]+)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/(?P<event_slug>[-_0-9A-Za-z]*)/(?P<pk>\d+)/$',
        views.occurrence_detail_redirect),
)
