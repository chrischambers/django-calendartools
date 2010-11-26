from calendartools.validators.defaults.occurrence import (
    activate_default_occurrence_validators
)
from calendartools.validators.defaults.attendance import (
    activate_default_attendance_validators
)

def activate_default_validators():
    activate_default_occurrence_validators()
    activate_default_attendance_validators()
