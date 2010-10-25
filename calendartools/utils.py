
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

