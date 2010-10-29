from datetime import datetime
from django.core.exceptions import ValidationError
from calendartools.signals import collect_occurrence_validators


class BaseValidator(object):
    priority = 10

    def __init__(self, sender, **kwargs):
        self.sender = sender
        self.kwargs = kwargs

    def validate(self):
        """Raises ValidationError if validation is unsuccessful."""
        raise NotImplementedError


class FinishGTStartValidator(BaseValidator):
    def validate(self):
        if self.sender.start >= self.sender.finish:
            raise ValidationError(
                'Finish date/time must be greater than start date/time.'
            )


class FutureOccurrencesOnlyValidator(BaseValidator):
    def validate(self):
        if not self.sender.id and self.sender.start < datetime.now():
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
