from threaded_multihost.threadlocals import get_current_request


class BaseValidator(object):
    """
    All Validation checks should inherit from this base-class, and implement
    their own ``validate`` method. Higher priority checks will be run first.
    """
    priority = 10

    def __init__(self, sender, **kwargs):
        self.sender = sender
        self.request = get_current_request()
        self.user = getattr(self.request, 'user', None)
        self.kwargs = kwargs

    def validate(self):
        """Raises ValidationError if validation is unsuccessful."""
        raise NotImplementedError


class BaseOccurrenceValidator(BaseValidator):
    def __init__(self, sender, **kwargs):
        super(BaseOccurrenceValidator, self).__init__(sender, **kwargs)
        self.occurrence = self.sender


class BaseUserAttendanceValidator(BaseValidator):
    def __init__(self, sender, **kwargs):
        super(BaseUserAttendanceValidator, self).__init__(sender, **kwargs)
        self.attendance = self.sender
