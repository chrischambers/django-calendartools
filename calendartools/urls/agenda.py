from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^$', views.today_agenda, {'slug': ''}),
    url(r'^(?P<year>\d{4})/$', views.year_agenda, {'slug': ''}),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/$', views.month_agenda, {'slug': ''}),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$', views.day_agenda, {'slug': ''}),

    url(r'^(?P<slug>[-A-Za-z_]*)/$', views.today_agenda, name='agenda'),
    url(r'^(?P<slug>[-A-Za-z_]*)/(?P<year>\d{4})/$',
        views.year_agenda, name='year-agenda'),
    url(r'^(?P<slug>[-A-Za-z_]*)/(?P<year>\d{4})/(?P<month>\w{3})/$',
        views.month_agenda, name='month-agenda'),
    url(r'^(?P<slug>[-A-Za-z_]*)/(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>[0-3]?\d)/$',
        views.day_agenda, name='day-agenda'),
)

