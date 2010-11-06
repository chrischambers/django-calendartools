from datetime import datetime, date

def current_datetime(request):
    data = {
        'now':   datetime.now(),
        'today': date.today(),
    }
    return data
