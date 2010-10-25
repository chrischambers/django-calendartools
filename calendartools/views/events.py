from calendartools.models import Event, Occurrence
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import list_detail

def event_list(request, *args, **kwargs):
    kwargs.update({
        'queryset': Event.objects.all(),
        'template_name': 'calendar/event_list.html'
    })
    return list_detail.object_list(request, *args, **kwargs)

def event_detail(request, slug, *args, **kwargs):
    kwargs.update({
        'queryset': Event.objects.all(),
        'slug': slug,
        'template_object_name': 'event',
        'template_name': 'calendar/event_detail.html'
    })
    return list_detail.object_detail(request, *args, **kwargs)

def event_create(request, *args, **kwargs):
    pass

def occurrence_detail(request, slug, pk, *args, **kwargs):
    occurrence = get_object_or_404(
        Occurrence.objects.filter(event__slug=slug),
        pk=pk
    )
    data = {'occurrence': occurrence, 'event': occurrence.event}
    return render_to_response("calendar/occurrence_detail.html", data,
                            context_instance=RequestContext(request))

