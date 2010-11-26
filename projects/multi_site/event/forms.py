from django.contrib.sites.models import Site
from django import forms
from event.models import Calendar, Event

class AdminAddCalendarForm(forms.ModelForm):
    sites = forms.ModelMultipleChoiceField(
        Site.objects.all(), initial=[Site.objects.get_current()]
    )


    class Meta(object):
        model = Calendar


class AdminAddEventForm(forms.ModelForm):
    sites = forms.ModelMultipleChoiceField(
        Site.objects.all(), initial=Site.objects.all()
    )


    class Meta(object):
        model = Event
