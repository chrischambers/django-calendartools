from datetime import datetime
from django.core.exceptions import ValidationError
from django.db.models.loading import get_model
from calendartools import defaults, signals
from calendartools.validators.base import BaseValidator


class BaseOccurrenceValidator(BaseValidator):
    def __init__(self, sender, instance, **kwargs):
        super(BaseOccurrenceValidator, self).__init__(
            sender, instance, **kwargs
        )
        self.occurrence = self.instance


class FinishGTStartValidator(BaseOccurrenceValidator):
    def validate(self):
        if self.occurrence.start >= self.occurrence.finish:
            raise ValidationError(
                'Finish date/time must be greater than start date/time.'
            )


class FutureOccurrencesOnlyValidator(BaseOccurrenceValidator):
    def validate(self):
        if not self.occurrence.pk and self.occurrence.start < datetime.now():
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


def activate_default_occurrence_validators():
    Occurrence = get_model(defaults.CALENDAR_APP_LABEL, 'Occurrence')
    signals.collect_validators.connect(
        FinishGTStartValidator,
        sender=Occurrence
    )
    signals.collect_validators.connect(
        FutureOccurrencesOnlyValidator,
        sender=Occurrence
    )
    signals.collect_validators.connect(
        MaxOccurrenceLengthValidator,
        sender=Occurrence
    )
    signals.collect_validators.connect(
        MinOccurrenceLengthValidator,
        sender=Occurrence
    )

def deactivate_default_occurrence_validators():
    Occurrence = get_model(defaults.CALENDAR_APP_LABEL, 'Occurrence')
    signals.collect_validators.disconnect(
        FinishGTStartValidator,
        sender=Occurrence
    )
    signals.collect_validators.disconnect(
        FutureOccurrencesOnlyValidator,
        sender=Occurrence
    )
    signals.collect_validators.disconnect(
        MaxOccurrenceLengthValidator,
        sender=Occurrence
    )
    signals.collect_validators.disconnect(
        MinOccurrenceLengthValidator,
        sender=Occurrence
    )
