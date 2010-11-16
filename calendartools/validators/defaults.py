from datetime import datetime
from django.core.exceptions import ValidationError
from calendartools.signals import collect_occurrence_validators
from calendartools.validators.base import BaseValidator


class FinishGTStartValidator(BaseValidator):
    def validate(self):
        if self.occurrence.start >= self.occurrence.finish:
            raise ValidationError(
                'Finish date/time must be greater than start date/time.'
            )


class FutureOccurrencesOnlyValidator(BaseValidator):
    def validate(self):
        if not self.occurrence.id and self.occurrence.start < datetime.now():
            raise ValidationError(
                'Event occurrences cannot be created in the past.'
            )

def activate_default_validators():
    collect_occurrence_validators.connect(
        FinishGTStartValidator
    )
    collect_occurrence_validators.connect(
        FutureOccurrencesOnlyValidator
    )
