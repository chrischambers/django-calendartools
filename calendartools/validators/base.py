class BaseValidator(object):
    """
    All Occurrence Validation checks should inherit from this base-class, and
    implement their own ``validate`` method. Higher priority checks will be run
    first.
    """
    priority = 10

    def __init__(self, sender, **kwargs):
        self.sender = sender
        self.kwargs = kwargs

    def validate(self):
        """Raises ValidationError if validation is unsuccessful."""
        raise NotImplementedError
