from threaded_multihost.threadlocals import get_current_request


class BaseValidator(object):
    """
    All Validation checks should inherit from this base-class, and implement
    their own ``validate`` method. Higher priority checks will be run first.
    """
    priority = 10

    def __init__(self, sender, instance, **kwargs):
        self.sender = sender
        self.instance = instance
        self.request = get_current_request()
        self.user = getattr(self.request, 'user', None)
        self.kwargs = kwargs

    def validate(self):
        """Raises ValidationError if validation is unsuccessful."""
        raise NotImplementedError
