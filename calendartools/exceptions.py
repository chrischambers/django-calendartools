class MaxOccurrenceCreationsExceeded(Exception):
    """Raised when ``Event.add_occurrences`` creates more instances than
    defaults.MAX_OCCURRENCE_CREATION_COUNT specifies."""
    pass
