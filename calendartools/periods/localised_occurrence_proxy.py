from calendartools.periods.proxybase import SimpleProxy
from django.conf import settings
from timezones.utils import localtime_for_timezone
import pytz

try:
    from functools import partial
except ImportError: # Python 2.3, 2.4 fallback.
    from django.utils.functional import curry as partial


class LocalizedOccurrenceProxy(SimpleProxy):
    def __init__(self, obj, timezone, *args, **kwargs):
        super(LocalizedOccurrenceProxy, self).__init__(obj, *args, **kwargs)
        self.timezone = timezone
        # rationalise to actual pytz.timezone

    def _get_datetime_attr(self, attrname):
        dt = getattr(self._obj, attrname)
        return localtime_for_timezone(dt, self.timezone)

    def _set_datetime_attr(self, value, attrname):
        if value.tzinfo is not None:
            value = value.astimezone(self.default_timezone).replace(tzinfo=None)
        setattr(self._obj, attrname, value)

    def _datetime_attr_doc(self, attrname):
        return getattr(self._obj, attrname).__doc__

    start = property(
        fget=partial(_get_datetime_attr, attrname='start'),
        fset=partial(_set_datetime_attr, attrname='start'),
        doc= partial(_datetime_attr_doc, attrname='start')
    )
    finish = property(
        fget=partial(_get_datetime_attr, attrname='finish'),
        fset=partial(_set_datetime_attr, attrname='finish'),
        doc= partial(_datetime_attr_doc, attrname='finish')
    )

    @property
    def real_start(self):
        return self._obj.start

    @property
    def real_finish(self):
        return self._obj.finish

    @property
    def default_timezone(self):
        return pytz.timezone(settings.TIME_ZONE)
