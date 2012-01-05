from datetime import datetime
from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic import list_detail

from calendartools import forms, defaults, decorators
from django.db.models.loading import get_model

Event = get_model(defaults.CALENDAR_APP_LABEL, 'Event')
Occurrence = get_model(defaults.CALENDAR_APP_LABEL, 'Occurrence')
Attendance = get_model(defaults.CALENDAR_APP_LABEL, 'Attendance')

def event_list(request, *args, **kwargs):
    kwargs.update({
        'queryset': Event.objects.visible(),
        'template_name': 'calendar/event_list.html'
    })
    return list_detail.object_list(request, *args, **kwargs)

def event_detail(request, slug, template='calendar/event_detail.html',
                 event_form_class=forms.EventForm,
                 recurrence_form_class=forms.MultipleOccurrenceForm,
                 check_edit_events=defaults.change_event_permission_check,
                 check_add_occurrences=defaults.add_occurrence_permission_check,
                 list_occurrences=True, success_url=None, extra_context=None,
                 *args, **kwargs):

    success_url = success_url or request.path
    extra_context = extra_context or {}
    event = get_object_or_404(Event.objects.visible(request.user), slug=slug)
    event_form = recurrence_form = None

    can_edit_events = check_edit_events(request)
    can_add_occurrences = check_add_occurrences(request)

    data = {
        'event': event,
        'can_edit_events': can_edit_events,
        'can_add_occurrences': can_add_occurrences
    }

    if request.method == 'POST':
        if '_update' in request.POST and can_edit_events:
            event_form = event_form_class(request.POST, instance=event)
            if event_form.is_valid():
                event_form.save(event)
                return http.HttpResponseRedirect(success_url)
        elif '_add' in request.POST and can_add_occurrences:
            recurrence_form = recurrence_form_class(
                data=request.POST, event=event, request=request
            )
            if recurrence_form.is_valid():
                if recurrence_form.invalid_occurrences:
                    session_data = {
                        'event': recurrence_form.event,
                        'valid_occurrences': recurrence_form.valid_occurrences,
                        'invalid_occurrences': recurrence_form.invalid_occurrences,
                    }
                    request.session['occurrence_info'] = session_data
                    return http.HttpResponseRedirect(reverse('confirm-occurrences'))
                recurrence_form.save()
                return http.HttpResponseRedirect(success_url)
        else:
            return http.HttpResponseBadRequest('Bad Request')

    if not event_form:
        event_form = event_form_class(instance=event)
    if not recurrence_form:
        recurrence_form = recurrence_form_class(
            event=event,
            request=request,
            initial={'dtstart': datetime.now()}
        )

    if can_edit_events:
        data['event_form'] = event_form
    if can_add_occurrences:
        data['recurrence_form'] = recurrence_form
    if list_occurrences:
        data['occurrences'] = event.occurrences.select_related(
            'event', 'calendar').visible()

    data.update(extra_context)
    return render_to_response(template, data,
                            context_instance=RequestContext(request))

def event_create(request, *args, **kwargs):
    pass

def occurrence_detail(request, slug, pk, show_attending=True, *args, **kwargs):
    occurrence = get_object_or_404(
        Occurrence.objects.visible(request.user).filter(
            event__slug=slug).select_related('event', 'calendar'),
            pk=pk
    )
    user = request.user
    if not user.is_authenticated():
        attendance = None
    else:
        try:
            attendance = Attendance.objects.get(
                user=user,
                occurrence=occurrence,
                status__in=[Attendance.STATUS.booked, Attendance.STATUS.attended]
            )
        except Attendance.DoesNotExist:
            attendance = Attendance(user=user, occurrence=occurrence)

    if request.method == 'POST' and attendance:
        form = forms.AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(
                reverse("occurrence-detail", args=(slug, pk))
            )
    else:
        form = forms.AttendanceForm(instance=attendance)

    data = {
        'event': occurrence.event,
        'attendance': attendance,
        'occurrence': occurrence,
    }
    if attendance and attendance.status != attendance.STATUS.attended:
        data['form'] = form
    if show_attending:
        data['attending'] = Attendance.objects.filter(occurrence=occurrence)

    return render_to_response("calendar/occurrence_detail.html", data,
                            context_instance=RequestContext(request))

@decorators.get_occurrence_data_from_session
def confirm_occurrences(request, event, valid_occurrences, invalid_occurrences,
                        FormClass=forms.ConfirmOccurrenceForm,
                        check_add_occurrences=defaults.add_occurrence_permission_check,
                        next=None, *args, **kwargs):

    next = next or reverse('event-detail', args=[event.slug])
    if not check_add_occurrences(request):
        return http.HttpResponseRedirect(next)

    if request.method == 'POST':
        form = FormClass(event, valid_occurrences, invalid_occurrences,
                         data=request.POST)
        if form.is_valid():
            if form.invalid_occurrences:
                session_data = {
                    'event':   form.event,
                    'valid_occurrences': form.valid_occurrences,
                    'invalid_occurrences': form.invalid_occurrences,
                }
                request.session['occurrence_info'] = session_data
                return http.HttpResponseRedirect(reverse('confirm-occurrences'))
            form.save()
            request.session.pop('occurrence_info', None)
            return http.HttpResponseRedirect(next)
    else:
        form = FormClass(event, valid_occurrences, invalid_occurrences)

    data = {
        'form':                form,
        'next':                next,
        'event':               event,
        'valid_occurrences':   valid_occurrences,
        'invalid_occurrences': invalid_occurrences,
    }

    return render_to_response("calendar/occurrence_confirm.html", data,
                            context_instance=RequestContext(request))

