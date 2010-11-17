
def time_delta_total_seconds(time_delta):
    '''
    Calculate the total number of seconds represented by a
    ``datetime.timedelta`` object.

    >>> from datetime import timedelta
    >>> time_delta_total_seconds(timedelta(0))
    0
    >>> time_delta_total_seconds(timedelta(1))
    86400
    >>> time_delta_total_seconds(timedelta(days=1, seconds=10))
    86410
    >>> time_delta_total_seconds(timedelta(days=1, hours=1))
    90000
    >>> time_delta_total_seconds(timedelta(hours=1, seconds=10))
    3610
    '''
    return int(time_delta.total_seconds())

import calendar
DAY_MAP = [
    calendar.SUNDAY,
    calendar.MONDAY,
    calendar.TUESDAY,
    calendar.WEDNESDAY,
    calendar.THURSDAY,
    calendar.FRIDAY,
    calendar.SATURDAY,
]
def determine_standardised_first_day_of_week():
    """
    Django's FIRST_DAY_OF_WEEK setting runs from 0-6, Sunday through Saturday
    (American Convention - apparently for implementation reasons, see:
    http://code.djangoproject.com/ticket/1061).Python's datetime, dateutil and
    calendar modules all use 0-6, Monday through Sunday. This function infers
    the 'standardised' version from the django setting.
    >>> from django.conf import settings
    >>> settings.FIRST_DAY_OF_WEEK = 0 # Sunday
    >>> determine_standardised_first_day_of_week()
    6
    >>> settings.FIRST_DAY_OF_WEEK = 1 # Monday
    >>> determine_standardised_first_day_of_week()
    0
    >>> settings.FIRST_DAY_OF_WEEK = 6 # Saturday
    >>> determine_standardised_first_day_of_week()
    5
    """
    from django.conf import settings
    return DAY_MAP[settings.FIRST_DAY_OF_WEEK]
