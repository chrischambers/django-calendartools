'''
Convenience forms for adding and updating ``Event`` and ``Occurrence``s.

'''
import logging
from datetime import datetime, date, time, timedelta
from dateutil import rrule
from pprint import pformat

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _
from django.forms.extras.widgets import SelectDateWidget

from calendartools.models import Event, Calendar, Attendance
from calendartools.constants import (
    WEEKDAY_SHORT, WEEKDAY_LONG,
    MONTH_SHORT, ORDINAL,
    FREQUENCY_CHOICES, REPEAT_CHOICES, ISO_WEEKDAYS_MAP
)
from calendartools.fields import MultipleIntegerField
from calendartools.defaults import (
    MINUTES_INTERVAL, SECONDS_INTERVAL, default_timeslot_offset_options,
    MAX_OCCURRENCE_CREATION_COUNT
)

log = logging.getLogger('calendartools.forms')

# Form Validaton Helpers:
greater_than_1 = MinValueValidator(1)
less_than_max  = MaxValueValidator(MAX_OCCURRENCE_CREATION_COUNT - 1)


class AttendanceForm(forms.ModelForm):
    # Necessary to hide all the other fields:
    noop = forms.CharField(required=False, widget=forms.widgets.HiddenInput())

    class Meta(object):
        model = Attendance
        fields = ['noop']

    def clean(self):
        if self.instance.pk and self.instance.status == Attendance.BOOKED:
            self.instance.status = Attendance.CANCELLED
        return self.cleaned_data


class EventForm(forms.ModelForm):
    '''
    A simple form for adding and updating Event attributes

    '''


    class Meta(object):
        model = Event
        fields = ('name', 'description',)


class OccurrenceBaseForm(forms.Form):
    def validate_occurrences(self):
        if not self.is_valid():
            raise ValueError

        self.valid_occurrences   = []
        self.invalid_occurrences = []
        # if not hasattr(self, 'invalid_occurrences'):
        #     self.invalid_occurrences = []

        for oc in self.occurrences:
            try:
                oc.full_clean()
                self.valid_occurrences.append(oc)
            except forms.ValidationError, e:
                errmsg = e.messages[0]
                self.invalid_occurrences.append((oc, errmsg))

        return (self.valid_occurrences, self.invalid_occurrences)

    def save(self):
        for occurrence in self.occurrences:
            occurrence.save()
        return self.occurrences


class MultipleOccurrenceForm(OccurrenceBaseForm):
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
    calendar = forms.ModelChoiceField(Calendar.objects.visible())
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
        widget=forms.TextInput(attrs=dict(size=2, max_length=2)),
        validators=[greater_than_1, less_than_max],
    )

    until = forms.DateField(
        required=False,
        initial=date.today,
        widget=SelectDateWidget(),
    )

    freq = forms.IntegerField(
        label=_(u'Frequency'),
        initial=rrule.WEEKLY,
        widget=forms.RadioSelect(choices=FREQUENCY_CHOICES),
    )

    interval = forms.IntegerField(
        initial='1',
        widget=forms.TextInput(attrs=dict(size=3, max_length=3)),
        validators=[greater_than_1, less_than_max],
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

    is_year_month_ordinal = forms.BooleanField(required=False)
    year_month_ordinal = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=ORDINAL))
    year_month_ordinal_day = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=WEEKDAY_LONG)
    )

    def __init__(self, event, *args, **kws):
        self.event = event
        self.request = kws.pop('request', None)
        self.user = getattr(self.request, 'user', None)
        super(MultipleOccurrenceForm, self).__init__(*args, **kws)

        self.fields['calendar'].choices = Calendar.objects.visible(
            self.user).values_list('id', 'name')

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
        self.cleaned_data.pop(fieldname, None)
        self._errors.setdefault(fieldname, self.error_class([errmsg]))

    def check_for_required_fields(self):
        """Many fields on this form depend on the values of other fields to
        determine whether they are required or not. This method handles those
        checks as part of the cleaning process."""

        if (not self.cleaned_data.get('repeats') or
            self.cleaned_data.get('freq') is None):
            # required fields not provided, let default validators handle:
            return

        required_errmsg = forms.Field.default_error_messages['required']

        if (self.cleaned_data['repeats'] == 'count' and
            not self.cleaned_data.get('count')):
            self.add_field_error('count', required_errmsg)

        if (self.cleaned_data['repeats'] == 'until' and
            not self.cleaned_data.get('until')):
            self.add_field_error('until', required_errmsg)

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

    def check_until_later_than_finish_datetime(self):
        repeats = self.cleaned_data.get('repeats')
        until = self.cleaned_data.get('until')
        if (until and repeats and repeats == 'until'
            and until <= self.cleaned_data['end_time'].date()):
            raise forms.ValidationError(_("'Until' date must occur in the future."))

    def clean(self):
        self.check_for_required_fields()

        day = datetime.combine(self.cleaned_data['day'], time(0))
        self.cleaned_data['start_time'] = day + timedelta(
            seconds=self.cleaned_data['start_time_delta']
        )
        self.cleaned_data['end_time'] = day + timedelta(
            seconds=self.cleaned_data['end_time_delta']
        )

        self.check_until_later_than_finish_datetime()
        log.debug("Recurrence-form, Cleaned Data\n%s" % (
            pformat(self.cleaned_data))
        )
        return self.cleaned_data

    def _post_clean(self):
        if self._errors:
            return

        if self.cleaned_data['repeats'] == 'no':
            self.rrules = {}
        else:
            self.rrules = self._build_rrule_params()

        self.occurrences = self.event.add_occurrences(
            self.cleaned_data['calendar'],
            self.cleaned_data['start_time'],
            self.cleaned_data['end_time'],
            commit=False,
            **self.rrules
        )

        self.validate_occurrences()
        return self.occurrences

    def validate_occurrences(self):
        if not self.is_valid():
            raise ValueError

        self.valid_occurrences   = []
        self.invalid_occurrences = []

        for oc in self.occurrences:
            try:
                oc.full_clean()
                self.valid_occurrences.append(oc)
            except forms.ValidationError, e:
                errmsg = e.messages[0]
                self.invalid_occurrences.append((oc, errmsg))

        return (self.valid_occurrences, self.invalid_occurrences)

    def save(self):
        for occurrence in self.occurrences:
            occurrence.save()
        return self.occurrences

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


class ConfirmOccurrenceForm(OccurrenceBaseForm):
    def __init__(self, event, valid_occurrences, invalid_occurrences, *args, **kws):
        self.event = event
        self.occurrences = valid_occurrences
        self.invalid_occurrences = invalid_occurrences

        super(ConfirmOccurrenceForm, self).__init__(*args, **kws)

    def _post_clean(self):
        if self._errors:
            return

        self.validate_occurrences()
        return self.occurrences
