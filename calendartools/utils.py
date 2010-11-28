from django.conf import settings

def timedelta_to_total_seconds(timedelta):
    '''
    Calculate the total number of seconds represented by a
    ``datetime.timedelta`` object.

    >>> from datetime import timedelta
    >>> timedelta_to_total_seconds(timedelta(0))
    0
    >>> timedelta_to_total_seconds(timedelta(1))
    86400
    >>> timedelta_to_total_seconds(timedelta(days=1, seconds=10))
    86410
    >>> timedelta_to_total_seconds(timedelta(days=1, hours=1))
    90000
    >>> timedelta_to_total_seconds(timedelta(hours=1, seconds=10))
    3610
    '''
    # Python 2.7 only!
    # return int(timedelta.total_seconds())
    hours_in_day, minutes_in_hour, seconds_in_minute = 24, 60, 60
    return ((timedelta.days * hours_in_day *
             minutes_in_hour * seconds_in_minute) + timedelta.seconds)

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
def standardise_first_dow(first_day_of_week=None):
    """
    Django's FIRST_DAY_OF_WEEK setting runs from 0-6, Sunday through Saturday
    (American Convention - apparently for implementation reasons, see:
    http://code.djangoproject.com/ticket/1061). Python's datetime, dateutil and
    calendar modules all use 0-6, Monday through Sunday. This function infers
    the 'standardised' version from the django setting.
    >>> from django.conf import settings
    >>> settings.FIRST_DAY_OF_WEEK = 0 # Sunday
    >>> standardise_first_dow()
    6
    >>> settings.FIRST_DAY_OF_WEEK = 1 # Monday
    >>> standardise_first_dow()
    0
    >>> settings.FIRST_DAY_OF_WEEK = 6 # Saturday
    >>> standardise_first_dow()
    5
    """
    if not first_day_of_week:
        first_day_of_week = settings.FIRST_DAY_OF_WEEK
    return DAY_MAP[first_day_of_week]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
