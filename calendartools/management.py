"""
Creates a default Calendar object.

"""

from django.db.models import signals
from calendartools.models import Calendar
from calendartools import models as calendar_app

def create_default_calendar(app, created_models, verbosity, db, **kwargs):
    if Calendar in created_models:
        if verbosity >= 2:
            print "Creating Calendar object"
        c = Calendar(name="Default", slug="")
        c.save(using=db)

signals.post_syncdb.connect(create_default_calendar, sender=calendar_app)
