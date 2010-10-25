from datetime import datetime
from django import http
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import list_detail

from calendartools.models import Event, Occurrence
from calendartools import forms

def event_list(request, *args, **kwargs):
    kwargs.update({
        'queryset': Event.objects.all(),
        'template_name': 'calendar/event_list.html'
    })
    return list_detail.object_list(request, *args, **kwargs)

def event_detail(request, slug, template='calendar/event_detail.html',
                 event_form_class=forms.EventForm,
                 recurrence_form_class=forms.MultipleOccurrenceForm,
                 success_url=None, extra_context=None):

    success_url = success_url or request.path
    extra_context = extra_context or {}
    event = get_object_or_404(Event, slug=slug)
    event_form = recurrence_form = None

    if request.method == 'POST':
        if '_update' in request.POST:
            event_form = event_form_class(request.POST, instance=event)
            if event_form.is_valid():
                event_form.save(event)
                return http.HttpResponseRedirect(success_url)
        elif '_add' in request.POST:
            recurrence_form = recurrence_form_class(request.POST)
            if recurrence_form.is_valid():
                recurrence_form.save(event)
                return http.HttpResponseRedirect(success_url)
        else:
            return http.HttpResponseBadRequest('Bad Request')

    if not event_form:
        event_form = event_form_class(instance=event)
    if not recurrence_form:
        recurrence_form = recurrence_form_class(
            initial={'dtstart': datetime.now()}
        )

    data = {
        'event': event,
        'event_form': event_form,
        'recurrence_form': recurrence_form
    }
    data.update(extra_context)
    return render_to_response(template, data,
                            context_instance=RequestContext(request))

def event_create(request, *args, **kwargs):
    pass

def occurrence_detail(request, slug, pk, *args, **kwargs):
    occurrence = get_object_or_404(
        Occurrence.objects.filter(event__slug=slug).select_related('event'),
        pk=pk
    )
    data = {'occurrence': occurrence, 'event': occurrence.event}
    return render_to_response("calendar/occurrence_detail.html", data,
                            context_instance=RequestContext(request))

