from datetime import datetime, date, time, timedelta
from django.conf import settings
from calendartools.utils import time_delta_total_seconds

# A "strftime" string for formatting start and end time selectors in forms
TIMESLOT_TIME_FORMAT = '%I:%M %p'

# Used for creating start and end time form selectors as well as time slot grids.
# Value should be datetime.timedelta value representing the incremental
# differences between temporal options
TIMESLOT_INTERVAL = timedelta(minutes=15)

# A datetime.time value indicting the starting time for time slot grids and form
# selectors
TIMESLOT_START_TIME = time(9)

# A datetime.timedelta value indicating the offset value from
# TIMESLOT_START_TIME for creating time slot grids and form selectors. The
# reason for using a time delta is that it possible to span dates. For
# instance, one could have a starting time of 3pm (15:00) and wish to indicate
# a ending value 1:30am (01:30), in which case a value of
# datetime.timedelta(hours=10.5) could be specified to indicate that the 1:30
# represents the following date's time and not the current date.
TIMESLOT_END_TIME_DURATION = timedelta(hours=+8)

# Indicates a minimum value for the number grid columns to be shown in the time
# slot table.
TIMESLOT_MIN_COLUMNS = 4

# Indicate the default length in time for a new occurrence, specifed by using
# a datetime.timedelta object
DEFAULT_OCCURRENCE_DURATION = timedelta(hours=+1)

# If not None, passed to the calendar module's setfirstweekday function.
CALENDAR_FIRST_WEEKDAY = 6

def view_hidden_events_check(request=None, user=None):
    user = request and request.user or user
    if not user:
        raise ValueError(
            'Either request or user must be supplied to validate.'
        )
    return user.is_superuser or user.is_staff

view_hidden_occurrences_check = view_hidden_events_check

def add_occurrence_permission_check(request):
    return request.user.has_perm('calendartools.add_occurrence')

def change_event_permission_check(request):
    return request.user.has_perm('calendartools.change_event')

# ----------------------------------------------------------------------------
MINUTES_INTERVAL = getattr(
    settings, 'TIMESLOT_INTERVAL', TIMESLOT_INTERVAL).seconds // 60

SECONDS_INTERVAL = time_delta_total_seconds(getattr(
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

    delta = time_delta_total_seconds(dtstart - dt)
    seconds = time_delta_total_seconds(interval)
    while dtstart <= dtend:
        options.append((delta, dtstart.strftime(fmt)))
        dtstart += interval
        delta += seconds

    return options

default_timeslot_options = timeslot_options()
default_timeslot_offset_options = timeslot_offset_options()
