import django.dispatch

collect_occurrence_validators = django.dispatch.Signal(
    providing_args=[]
)

collect_user_attendance_validators = django.dispatch.Signal(
    providing_args=[]
)
