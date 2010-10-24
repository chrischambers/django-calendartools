def event_list(request, *args, **kwargs):
    pass

def event_detail(request, *args, **kwargs):
    pass

def event_create(request, *args, **kwargs):
    pass

def occurrence_detail(request, *args, **kwargs):
    data = {}
    return render_to_response("calendar/occurrence_detail.html", data,
                            context_instance=RequestContext(request))

