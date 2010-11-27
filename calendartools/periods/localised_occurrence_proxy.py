from calendartools.periods.proxybase import SimpleProxy
from django.conf import settings
from timezones.utils import localtime_for_timezone
import pytz


class LocalizedOccurrenceProxy(SimpleProxy):
    def __init__(self, obj, timezone, *args, **kwargs):
        super(LocalizedOccurrenceProxy, self).__init__(obj, *args, **kwargs)
        self.timezone = timezone
        self.occurrence = obj
        # rationalise to actual pytz.timezone
        # self.create_localised_datetime_proxy_attrs('start', 'finish')
        # self.create_real_properties('start', 'finish')

    @property
    def real_start(self):
        return self._obj.start

    @property
    def real_finish(self):
        return self._obj.finish

    def _get_start(self):
        dt = self._obj.start
        return localtime_for_timezone(dt, self.timezone)

    def _set_start(self, value):
        # value = localtime_for_timezone(value, self.default_timezone)
        ## convert to settings.TIME_ZONE
        if value.tzinfo is not None:
            value = value.astimezone(self.default_timezone).replace(tzinfo=None)
        self._obj.start = value

    start = property(_get_start, _set_start)

    def _get_finish(self):
        dt = self._obj.finish
        return localtime_for_timezone(dt, self.timezone)

    def _set_finish(self, value):
        # value = localtime_for_timezone(value, self.default_timezone)
        ## convert to settings.TIME_ZONE
        if value.tzinfo is not None:
            value = value.astimezone(self.default_timezone).replace(tzinfo=None)
        self._obj.finish = value

    finish = property(fget=_get_finish, fset=_set_finish)
    # def create_real_properties(self, *args):
    #     for attr in args:
    #         def real_property():
    #             doc = getattr(self.occurrence, attr).__doc__
    #             def fget(self):
    #                 return getattr(self.occurrence, attr)
    #             def fset(self, value):
    #                 setattr(self.occurrence, attr, value)
    #             return {'doc': doc, 'fget': fget, 'fset': fset}
    #         setattr(self.__class__, 'real_%s' % attr, property(**real_property()))

    @property
    def default_timezone(self):
        return pytz.timezone(settings.TIME_ZONE)

    # def create_localised_datetime_proxy_attrs(self, *args):
    #     for attr in args:
    #         def real_property():
    #             doc = getattr(self.occurrence, attr).__doc__
    #             def fget(self):
    #                 dt = getattr(self.occurrence, attr)
    #                 dt.replace(tzinfo=self.default_timezone)
    #                 dt = localtime_for_timezone(dt, self.timezone)
    #                 return dt
    #             def fset(self, value):
    #                 value = localtime_for_timezone(value, self.default_timezone)
    #                 setattr(self.occurrence, attr, value)
    #             return {'doc': doc, 'fget': fget, 'fset': fset}
    #         setattr(self.__class__, attr, property(**real_property()))
