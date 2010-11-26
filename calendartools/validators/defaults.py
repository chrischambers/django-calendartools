from datetime import datetime
from django.db.models.loading import get_model
from django.core.exceptions import ValidationError
from calendartools import defaults
from calendartools.signals import collect_validators
from calendartools.validators.base import (
    BaseOccurrenceValidator, BaseUserAttendanceValidator
)


class FinishGTStartValidator(BaseOccurrenceValidator):
    def validate(self):
        if self.occurrence.start >= self.occurrence.finish:
            raise ValidationError(
                'Finish date/time must be greater than start date/time.'
            )


class FutureOccurrencesOnlyValidator(BaseOccurrenceValidator):
    def validate(self):
        if not self.occurrence.id and self.occurrence.start < datetime.now():
            raise ValidationError(
                'Event occurrences cannot be created in the past.'
            )


class MaxOccurrenceLengthValidator(BaseOccurrenceValidator):
    def validate(self):
        max_length = defaults.MAX_OCCURRENCE_DURATION
        if max_length:
            length = self.occurrence.finish - self.occurrence.start
            if not length <= max_length:
                raise ValidationError(
                    'Events must be less than %s long.' % max_length
                )


class MinOccurrenceLengthValidator(BaseOccurrenceValidator):
    def validate(self):
        min_length = defaults.MIN_OCCURRENCE_DURATION
        if min_length:
            length = self.occurrence.finish - self.occurrence.start
            if not length >= min_length:
                raise ValidationError(
                    'Events must be greater than %s long.' % min_length
                )


class CannotBookFinishedEventsValidator(BaseUserAttendanceValidator):
    def validate(self):
        if (not self.attendance.id and
            self.attendance.occurrence.finish < datetime.now()):
            raise ValidationError(
                'Cannot book/attend events which have occurred in the past.'
            )


class CannotAttendFutureEventsValidator(BaseUserAttendanceValidator):
    def validate(self):
        if (self.attendance.status == self.attendance.ATTENDED and
            self.attendance.occurrence.start > datetime.now()):
            raise ValidationError(
                'Cannot attend events which have not yet occurred.'
            )


class OnlyOneActiveAttendanceForOccurrenceValidator(BaseUserAttendanceValidator):
    priority = 50

    def validate(self):
        Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')
        already_attending = Attendance.objects.filter(
            user=self.attendance.user,
            occurrence=self.attendance.occurrence,
            status__in=[Attendance.BOOKED, Attendance.ATTENDED]
        )
        if self.attendance.id:
            already_attending = already_attending.exclude(id=self.attendance.id)

        if already_attending.exists():
            raise ValidationError(
                'User already has an active attendance record for this event.'
            )

def activate_default_occurrence_validators():
    Occurrence = get_model(defaults.CALENDAR_APP_LABEL, 'Occurrence')
    collect_validators.connect(
        FinishGTStartValidator,
        sender=Occurrence
    )
    collect_validators.connect(
        FutureOccurrencesOnlyValidator,
        sender=Occurrence
    )
    collect_validators.connect(
        MaxOccurrenceLengthValidator,
        sender=Occurrence
    )
    collect_validators.connect(
        MinOccurrenceLengthValidator,
        sender=Occurrence
    )

def activate_default_attendance_validators():
    Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')
    collect_validators.connect(
        CannotBookFinishedEventsValidator,
        sender=Attendance
    )
    collect_validators.connect(
        CannotAttendFutureEventsValidator,
        sender=Attendance
    )
    collect_validators.connect(
        OnlyOneActiveAttendanceForOccurrenceValidator,
        sender=Attendance
    )

def activate_default_validators():
    activate_default_occurrence_validators()
    activate_default_attendance_validators()
