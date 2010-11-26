from django.contrib import admin
from django.db.models.loading import get_model
from calendartools import defaults


class CalendarAdmin(admin.ModelAdmin):
    raw_id_fields = ['creator', 'editor']
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('creator', 'editor', 'datetime_created', 'datetime_modified')
    list_display = ['name', 'slug', 'description', 'status', 'datetime_created']
    list_editable = ['status']
    date_hierarchy = "datetime_created"
    search_fields = ('name',)


class EventAdmin(CalendarAdmin):
    pass


class CancellationInline(admin.TabularInline):
    model = get_model(defaults.CALENDAR_APP_LABEL, 'Cancellation')
    readonly_fields = ('creator', 'editor', 'datetime_created', 'datetime_modified')


class OccurrenceAdmin(admin.ModelAdmin):
    raw_id_fields = ['creator', 'editor']
    readonly_fields = ('creator', 'editor', 'datetime_created', 'datetime_modified')
    list_display = ['calendar', 'event', 'start', 'finish', 'status',
                    'datetime_created']
    list_editable = ['status']
    date_hierarchy = "datetime_created"
    search_fields = ('event__name',)


class AttendanceAdmin(admin.ModelAdmin):
    raw_id_fields = ['creator', 'editor', 'user', 'occurrence']
    readonly_fields = ('creator', 'editor', 'datetime_created', 'datetime_modified')
    list_display = ['user', 'occurrence', 'status', 'datetime_created']
    list_editable = ['status']
    date_hierarchy = "datetime_created"
    inlines = [CancellationInline]

Calendar = get_model(defaults.CALENDAR_APP_LABEL, 'Calendar')
Event = get_model(defaults.CALENDAR_APP_LABEL, 'Event')
Occurrence = get_model(defaults.CALENDAR_APP_LABEL, 'Occurrence')
Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Occurrence, OccurrenceAdmin)
admin.site.register(Attendance, AttendanceAdmin)
