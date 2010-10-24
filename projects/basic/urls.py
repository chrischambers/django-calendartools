from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r"^calendar/", include('calendartools.urls')),
    (r'^admin/', include(admin.site.urls)),
)

# Serve Static Files on Development Machines:
# -- See http://docs.djangoproject.com/en/dev/howto/static-files/
if settings.DEBUG:
    urlpatterns += patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
    {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
)
