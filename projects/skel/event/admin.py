from django.contrib import admin
from event.models import (
    Calendar, Event, Occurrence, Attendance, Cancellation
)
from calendartools.admin import (
    CalendarAdmin, EventAdmin, OccurrenceAdmin, AttendanceAdmin
)

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Occurrence, OccurrenceAdmin)
admin.site.register(Attendance, AttendanceAdmin)

