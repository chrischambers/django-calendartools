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

def finish_gt_start(sender, **kwargs):
    if sender.start >= sender.finish:
        raise ValidationError(
            'Finish date/time must be greater than start date/time.'
        )

def create_occurrences_in_future_only(sender, **kwargs):
    if not sender.id and sender.start < datetime.now():
        raise ValidationError(
            'Event senders cannot be created in the past.'
        )


class FinishGTStartValidator(BaseValidator):
    def validate(self):
        return finish_gt_start(self.sender, **self.kwargs)


class FutureOccurrencesOnlyValidator(BaseValidator):
    def validate(self):
        return create_occurrences_in_future_only(self.sender, **self.kwargs)

def activate_default_validators():
    collect_occurrence_validators.connect(
        FinishGTStartValidator
    )
    collect_occurrence_validators.connect(
        FutureOccurrencesOnlyValidator
    )
