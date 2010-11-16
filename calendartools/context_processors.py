from datetime import datetime, date
from calendartools.periods import Day

def current_datetime(request):
    data = {
        'now':   datetime.now(),
        'today': Day(date.today()),
    }
    return data
