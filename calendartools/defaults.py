from datetime import datetime, date, time, timedelta
from django.conf import settings
from calendartools.utils import timedelta_to_total_seconds

# Enables a templatetag override which ensures that nothing within the {% url
# %} templatetag is translated.
NO_URL_TRANSLATION = True

CALENDAR_APP_LABEL = getattr(settings, 'CALENDAR_APP_LABEL', 'event')

# A "strftime" string for formatting start and end time selectors in forms
TIMESLOT_TIME_FORMAT = getattr(settings, 'TIMESLOT_TIME_FORMAT', '%I:%M %p')

# Used for creating start and end time form selectors as well as time slot grids.
# Value should be datetime.timedelta value representing the incremental
# differences between temporal options
TIMESLOT_INTERVAL = getattr(settings, 'TIMESLOT_INTERVAL', timedelta(minutes=15))

# A datetime.time value indicting the starting time for time slot grids and form
# selectors
TIMESLOT_START_TIME = getattr(settings, 'TIMESLOT_START_TIME', time(9))

# A datetime.timedelta value indicating the offset value from
# TIMESLOT_START_TIME for creating time slot grids and form selectors. The
# reason for using a time delta is that it possible to span dates. For
# instance, one could have a starting time of 3pm (15:00) and wish to indicate
# a ending value 1:30am (01:30), in which case a value of
# datetime.timedelta(hours=10.5) could be specified to indicate that the 1:30
# represents the following date's time and not the current date.
TIMESLOT_END_TIME_DURATION = getattr(settings, 'TIMESLOT_END_TIME_DURATION',
                                     timedelta(hours=+8))

# Indicates a minimum value for the number grid columns to be shown in the time
# slot table.
TIMESLOT_MIN_COLUMNS = getattr(settings, 'TIMESLOT_MIN_COLUMNS', 4)

# Indicate the default length in time for a new occurrence, specifed by using
# a datetime.timedelta object
DEFAULT_OCCURRENCE_DURATION = getattr(settings, 'DEFAULT_OCCURRENCE_DURATION',
                                      timedelta(hours=+1))

MIN_OCCURRENCE_DURATION = getattr(settings, 'MIN_OCCURRENCE_DURATION', None)
MAX_OCCURRENCE_DURATION = getattr(settings, 'MAX_OCCURRENCE_DURATION', None)

# If not None/0, raises a ``MaxOccurrenceCreationsExceeded`` Exception if the
# ``Event.add_occurrences`` utility function creates more Occurrence objects
# than specified. This is to mitigate the damage caused by unforeseen bugs
# which may result in ``rrule.rrule`` producing an iterable of unlimited
# length.
MAX_OCCURRENCE_CREATION_COUNT = getattr(settings, 'MAX_OCCURRENCE_CREATION_COUNT', 100)

# When set to a value > 0, the agenda views will be paginated by the value
# specified.
MAX_AGENDA_ITEMS_PER_PAGE = getattr(settings, 'MAX_AGENDA_ITEMS_PER_PAGE', 0)

def default_view_hidden_events_check(request=None, user=None):
    user = request and request.user or user
    if not user:
        raise ValueError(
            'Either request or user must be supplied to validate.'
        )
    return user.is_superuser or user.is_staff

view_hidden_events_check = getattr(
    settings, 'VIEW_HIDDEN_EVENTS_CHECK', None
)
view_hidden_occurrences_check = getattr(
    settings, 'VIEW_HIDDEN_OCCURRENCES_CHECK', None
)
view_hidden_calendars_check = getattr(
    settings, 'VIEW_HIDDEN_CALENDARS_CHECK', None
)
if not view_hidden_events_check:
    view_hidden_events_check = default_view_hidden_events_check
if not view_hidden_occurrences_check:
    view_hidden_occurrences_check = default_view_hidden_events_check
if not view_hidden_calendars_check:
    view_hidden_calendars_check = default_view_hidden_events_check

add_occurrence_permission_check = getattr(
    settings, 'ADD_OCCURRENCE_PERMISSION_CHECK', None
)
if not add_occurrence_permission_check:
    def add_occurrence_permission_check(request):
        return request.user.has_perm('%s.add_occurrence' % CALENDAR_APP_LABEL)

change_event_permission_check = getattr(
    settings, 'CHANGE_EVENT_PERMISSION_CHECK', None
)
if not change_event_permission_check:
    def change_event_permission_check(request):
        return request.user.has_perm('%s.change_event' % CALENDAR_APP_LABEL)

# ----------------------------------------------------------------------------
MINUTES_INTERVAL = getattr(
    settings, 'TIMESLOT_INTERVAL', TIMESLOT_INTERVAL).seconds // 60

SECONDS_INTERVAL = timedelta_to_total_seconds(getattr(
    settings, 'DEFAULT_OCCURRENCE_DURATION', DEFAULT_OCCURRENCE_DURATION)
)

def get_timeslot_defaults(interval, start_time, end_delta, fmt):
    if not interval:
        interval = getattr(settings, 'TIMESLOT_INTERVAL', TIMESLOT_INTERVAL)
    if not start_time:
        start_time = getattr(settings, 'TIMESLOT_START_TIME', TIMESLOT_START_TIME)
    if not end_delta:
        end_delta = getattr(
            settings, 'TIMESLOT_END_TIME_DURATION', TIMESLOT_END_TIME_DURATION)
    if not fmt:
        fmt = getattr(settings, 'TIMESLOT_TIME_FORMAT', TIMESLOT_TIME_FORMAT)
    return interval, start_time, end_delta, fmt

def timeslot_options(interval=None, start_time=None, end_delta=None, fmt=None):
    '''
    Create a list of time slot options for use in swingtime forms.

    The list is comprised of 2-tuples containing a 24-hour time value and a
    12-hour temporal representation of that offset.

    '''
    interval, start_time, end_delta, fmt = get_timeslot_defaults(
        interval, start_time, end_delta, fmt
    )
    dt = datetime.combine(date.today(), time(0))
    dtstart = datetime.combine(dt.date(), start_time)
    dtend = dtstart + end_delta
    options = []

    while dtstart <= dtend:
        options.append((str(dtstart.time()), dtstart.strftime(fmt)))
        dtstart += interval

    return options

def timeslot_offset_options(interval=None, start_time=None, end_delta=None,
                            fmt=None):
    '''
    Create a list of time slot options for use in swingtime forms.

    The list is comprised of 2-tuples containing the number of seconds since
    the start of the day and a 12-hour temporal representation of that offset.

    '''
    interval, start_time, end_delta, fmt = get_timeslot_defaults(
        interval, start_time, end_delta, fmt
    )
    dt = datetime.combine(date.today(), time(0))
    dtstart = datetime.combine(dt.date(), start_time)
    dtend = dtstart + end_delta
    options = []

    delta = timedelta_to_total_seconds(dtstart - dt)
    seconds = timedelta_to_total_seconds(interval)
    while dtstart <= dtend:
        options.append((delta, dtstart.strftime(fmt)))
        dtstart += interval
        delta += seconds

    return options

default_timeslot_options = getattr(settings, 'TIMESLOT_OPTIONS', None)
if not default_timeslot_options:
    default_timeslot_options = timeslot_options()
default_timeslot_offset_options = getattr(settings, 'TIMESLOT_OFFSET_OPTIONS', None)
if not default_timeslot_offset_options:
    default_timeslot_offset_options = timeslot_offset_options()
