from datetime import datetime
from django.core.exceptions import ValidationError
from calendartools.signals import (
    collect_occurrence_validators, collect_attendance_validators
)
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


class CannotAttendFinishedEventsValidator(BaseUserAttendanceValidator):
    def validate(self):
        if (not self.attendance.id and
            self.attendance.occurrence.finish < datetime.now()):
            raise ValidationError(
                'Cannot attend events which have occurred in the past.'
            )

def activate_default_occurrence_validators():
    collect_occurrence_validators.connect(
        FinishGTStartValidator
    )
    collect_occurrence_validators.connect(
        FutureOccurrencesOnlyValidator
    )

def activate_default_attendance_validators():
    collect_attendance_validators.connect(
        CannotAttendFinishedEventsValidator
    )

def activate_default_validators():
    activate_default_occurrence_validators()
    activate_default_attendance_validators()
