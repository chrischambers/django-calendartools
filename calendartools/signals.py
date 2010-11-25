import django.dispatch

collect_validators = django.dispatch.Signal(
    providing_args=['instance']
)
