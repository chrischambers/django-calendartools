
def time_delta_total_seconds(time_delta):
    '''
    Calculate the total number of seconds represented by a
    ``datetime.timedelta`` object.

    '''
    return time_delta.days * 3600 + time_delta.seconds

