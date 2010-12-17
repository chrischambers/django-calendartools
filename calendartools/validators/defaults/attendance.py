from datetime import datetime
from django.core.exceptions import ValidationError
from django.db.models.loading import get_model
from calendartools import defaults, signals
from calendartools.validators.base import BaseValidator


class BaseAttendanceValidator(BaseValidator):
    def __init__(self, sender, instance, **kwargs):
        super(BaseAttendanceValidator, self).__init__(
            sender, instance, **kwargs
        )
        self.attendance = self.instance


class CannotBookFinishedEventsValidator(BaseAttendanceValidator):
    def validate(self):
        if (not self.attendance.pk and
            self.attendance.occurrence.finish < datetime.now()):
            raise ValidationError(
                'Cannot book/attend events which have occurred in the past.'
            )


class CannotAttendFutureEventsValidator(BaseAttendanceValidator):
    def validate(self):
        if (self.attendance.status == self.attendance.STATUS.attended and
            self.attendance.occurrence.start > datetime.now()):
            raise ValidationError(
                'Cannot attend events which have not yet occurred.'
            )


class CannotCancelAttendedEventsValidator(BaseAttendanceValidator):
    def validate(self):
        if (self.attendance.status == self.attendance.STATUS.cancelled
            and self.attendance.pk):
            Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')
            try:
                previous_status = Attendance._default_manager.values_list(
                    'status', flat=True).get(pk=self.attendance.pk)
                if previous_status == self.attendance.STATUS.attended:
                    raise ValidationError(
                        'Cannot cancel attendance for events which have '
                        'already been attended.'
                    )
            except Attendance.DoesNotExist:
                pass


class OnlyOneActiveAttendanceForOccurrenceValidator(BaseAttendanceValidator):
    priority = 50

    def validate(self):
        Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')
        already_attending = Attendance._default_manager.filter(
            user=self.attendance.user,
            occurrence=self.attendance.occurrence,
            status__in=[Attendance.STATUS.booked, Attendance.STATUS.attended]
        )
        if self.attendance.pk:
            already_attending = already_attending.exclude(pk=self.attendance.pk)

        if already_attending.exists():
            raise ValidationError(
                'User already has an active attendance record for this event.'
            )

DEFAULT_VALIDATORS = [
    CannotBookFinishedEventsValidator,
    CannotAttendFutureEventsValidator,
    OnlyOneActiveAttendanceForOccurrenceValidator,
    CannotCancelAttendedEventsValidator,
]

def activate_default_attendance_validators():
    Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')

    for validator in DEFAULT_VALIDATORS:
        signals.collect_validators.connect(validator, sender=Attendance)

def deactivate_default_attendance_validators():
    Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')

    for validator in DEFAULT_VALIDATORS:
        signals.collect_validators.disconnect(validator, sender=Attendance)
