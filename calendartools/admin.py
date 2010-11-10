from django.contrib import admin
from calendartools.models import Calendar, Event, Occurrence

class CalendarAdmin(admin.ModelAdmin):
    pass

class EventAdmin(admin.ModelAdmin):
    raw_id_fields = ['creator', 'editor']
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('creator', 'editor', 'datetime_created', 'datetime_modified')
    list_display = ['name', 'slug', 'description', 'status', 'datetime_created']
    list_editable = ['status']
    date_hierarchy = "datetime_created"
    search_fields = ('name',)


class OccurrenceAdmin(admin.ModelAdmin):
    raw_id_fields = ['creator', 'editor']
    readonly_fields = ('creator', 'editor', 'datetime_created', 'datetime_modified')
    list_display = ['event', 'start', 'finish', 'status', 'datetime_created']
    list_editable = ['status']
    date_hierarchy = "datetime_created"
    search_fields = ('event__name',)

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Occurrence, OccurrenceAdmin)
