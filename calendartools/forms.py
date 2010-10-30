'''
Convenience forms for adding and updating ``Event`` and ``Occurrence``s.

'''
import logging
from datetime import datetime, date, time, timedelta
from dateutil import rrule
from pprint import pformat

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms.extras.widgets import SelectDateWidget

from calendartools.models import Event
from calendartools.constants import (
    WEEKDAY_SHORT, WEEKDAY_LONG,
    MONTH_SHORT, ORDINAL,
    FREQUENCY_CHOICES, REPEAT_CHOICES, ISO_WEEKDAYS_MAP
)
from calendartools.fields import MultipleIntegerField
from calendartools.defaults import (
    MINUTES_INTERVAL, SECONDS_INTERVAL, default_timeslot_offset_options,
)

log = logging.getLogger('calendartools.forms')


class EventForm(forms.ModelForm):
    '''
    A simple form for adding and updating Event attributes

    '''


    class Meta(object):
        model = Event
        fields = ('name', 'description',)


class MultipleOccurrenceForm(forms.Form):
    """
    day
    start_time_delta
    end_time_delta

    # recurrence options
    repeats
    count
    until
    freq
    interval

    # weekly options
    week_days

    # monthly options
    month_option
    month_ordinal
    month_ordinal_day
    each_month_day

    # yearly options
    year_months
    is_year_month_ordinal
    year_month_ordinal
    year_month_ordinal_day
    """
    day = forms.DateField(
        label=_(u'Date'),
        initial=date.today,
        widget=SelectDateWidget()
    )

    start_time_delta = forms.IntegerField(
        label=_(u'Start time'),
        widget=forms.Select(choices=default_timeslot_offset_options)
    )

    end_time_delta = forms.IntegerField(
        label=_(u'End time'),
        widget=forms.Select(choices=default_timeslot_offset_options)
    )

    # recurrence options
    repeats = forms.ChoiceField(
        choices=REPEAT_CHOICES,
        initial='count',
        label=_(u'Occurrences'),
        widget=forms.RadioSelect()
    )

    count = forms.IntegerField(
        label=_(u'Total Occurrences'),
        initial=1,
        required=False,
        widget=forms.TextInput(attrs=dict(size=2, max_length=2))
    )

    until = forms.DateField(
        required=False,
        initial=date.today,
        widget=SelectDateWidget()
    )

    freq = forms.IntegerField(
        label=_(u'Frequency'),
        initial=rrule.WEEKLY,
        widget=forms.RadioSelect(choices=FREQUENCY_CHOICES),
    )

    interval = forms.IntegerField(
        required=False,
        initial='1',
        widget=forms.TextInput(attrs=dict(size=3, max_length=3))
    )

    # weekly options
    week_days = MultipleIntegerField(
        WEEKDAY_SHORT,
        label=_(u'Weekly options'),
        widget=forms.CheckboxSelectMultiple
    )

    # monthly options
    month_option = forms.ChoiceField(
        choices=(('on',_(u'On the')), ('each',_(u'Each:'))),
        initial='each',
        required=False,
        widget=forms.RadioSelect(),
        label=_(u'Monthly options')
    )

    month_ordinal = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=ORDINAL)
    )
    month_ordinal_day = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=WEEKDAY_LONG)
    )
    each_month_day = MultipleIntegerField(
        [(i,i) for i in range(1,32)],
        widget=forms.CheckboxSelectMultiple
    )

    # yearly options
    year_months = MultipleIntegerField(
        MONTH_SHORT,
        label=_(u'Yearly options'),
        widget=forms.CheckboxSelectMultiple
    )

    is_year_month_ordinal = forms.NullBooleanField(required=False)
    year_month_ordinal = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=ORDINAL))
    year_month_ordinal_day = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=WEEKDAY_LONG)
    )

    def __init__(self, *args, **kws):
        super(MultipleOccurrenceForm, self).__init__(*args, **kws)
        dtstart = self.initial.get('dtstart', None)
        if dtstart:
            dtstart = dtstart.replace(
                minute=((dtstart.minute // MINUTES_INTERVAL) * MINUTES_INTERVAL),
                second=0,
                microsecond=0
            )

            weekday = dtstart.isoweekday()
            ordinal = dtstart.day // 7
            ordinal = u'%d' % (-1 if ordinal > 3 else ordinal + 1,)

            self.initial.setdefault('week_days', u'%d' % weekday)
            self.initial.setdefault('month_ordinal', ordinal)
            self.initial.setdefault('month_ordinal_day', u'%d' % weekday)
            self.initial.setdefault('each_month_day', [u'%d' % dtstart.day])
            self.initial.setdefault('year_months', [u'%d' % dtstart.month])
            self.initial.setdefault('year_month_ordinal', ordinal)
            self.initial.setdefault('year_month_ordinal_day', u'%d' % weekday)

            offset = (dtstart - datetime.combine(dtstart.date(), time(0))).seconds
            self.initial.setdefault('start_time_delta', u'%d' % offset)
            self.initial.setdefault('end_time_delta', u'%d' % (
                offset + SECONDS_INTERVAL,)
            )

    def add_field_error(self, fieldname, errmsg):
        """This will clobber any existing errors."""
        self.cleaned_data.pop(fieldname, None)
        self._errors['count'] = self.error_class([errmsg])

    def clean(self):
        if (not self.cleaned_data.get('repeats') or
            self.cleaned_data.get('freq') is None):
            return # required field not provided

        required_errmsg = forms.Field.default_error_messages['required']

        if (self.cleaned_data['repeats'] == 'count' and
            not self.cleaned_data.get('count')):
            self.add_field_error('count', required_errmsg)

        if (self.cleaned_data['repeats'] == 'until' and
            not self.cleaned_data.get('until')):
            self.add_field_error('until', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.DAILY and
            not self.cleaned_data.get('interval')):
            self.add_field_error('interval', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.WEEKLY and
            not self.cleaned_data.get('week_days')):
            self.add_field_error('week_days', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.MONTHLY and
            not self.cleaned_data.get('month_option')):
            self.add_field_error('month_options', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.MONTHLY and
            self.cleaned_data.get('month_option') == 'on' and
            not self.cleaned_data.get('month_ordinal')):
            self.add_field_error('month_ordinal', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.MONTHLY and
            self.cleaned_data.get('month_option') == 'on' and
            not self.cleaned_data.get('month_ordinal_day')):
            self.add_field_error('month_ordinal_day', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.MONTHLY and
            self.cleaned_data.get('month_option') == 'each' and
            not self.cleaned_data.get('each_month_day')):
            self.add_field_error('each_month_day', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.YEARLY and
            self.cleaned_data.get('is_year_month_ordinal') is None):
            self.add_field_error('is_year_month_ordinal', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.YEARLY and
            self.cleaned_data.get('is_year_month_ordinal') and
            not self.cleaned_data.get('year_month_ordinal')):
            self.add_field_error('year_month_ordinal', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.YEARLY and
            self.cleaned_data.get('is_year_month_ordinal') and
            not self.cleaned_data.get('year_month_ordinal_day')):
            self.add_field_error('year_month_ordinal_day', required_errmsg)

        if (self.cleaned_data['freq'] == rrule.YEARLY and
            self.cleaned_data.get('is_year_month_ordinal') is False and
            not self.cleaned_data.get('year_months')):
            self.add_field_error('year_months', required_errmsg)

        day = datetime.combine(self.cleaned_data['day'], time(0))
        self.cleaned_data['start_time'] = day + timedelta(
            seconds=self.cleaned_data['start_time_delta']
        )

        self.cleaned_data['end_time'] = day + timedelta(
            seconds=self.cleaned_data['end_time_delta']
        )

        log.debug("Recurrence-form, Cleaned Data\n%s" % pformat(self.cleaned_data))
        return self.cleaned_data

    def save(self, event):
        if self.cleaned_data['repeats'] == 'no':
            params = {}
        else:
            params = self._build_rrule_params()

        event.add_occurrences(
            self.cleaned_data['start_time'],
            self.cleaned_data['end_time'],
            **params
        )

        return event

    def _build_rrule_params(self):
        iso = ISO_WEEKDAYS_MAP
        data = self.cleaned_data
        params = dict(
            freq=data['freq'],
            interval=data['interval'] or 1
        )

        if self.cleaned_data['repeats'] == 'count':
            params['count'] = data['count']
        elif self.cleaned_data['repeats'] == 'until':
            params['until'] = data['until']

        if params['freq'] == rrule.WEEKLY:
            params['byweekday'] = [iso[n] for n in data['week_days']]

        elif params['freq'] == rrule.MONTHLY:
            if 'on' == data['month_option']:
                ordinal = data['month_ordinal']
                day = iso[data['month_ordinal_day']]
                params['byweekday'] = day(ordinal)
            else:
                params['bymonthday'] = data['each_month_day']

        elif params['freq'] == rrule.YEARLY:
            params['bymonth'] = data['year_months']
            if data['is_year_month_ordinal']:
                ordinal = data['year_month_ordinal']
                day = iso[data['year_month_ordinal_day']]
                params['byweekday'] = day(ordinal)

        elif params['freq'] != rrule.DAILY:
            raise NotImplementedError(
                _(u'Unknown interval rule %s') % params['freq']
            )

        return params

