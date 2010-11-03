from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

try:
    from functools import wraps
except ImportError: # Python 2.3, 2.4 fallback.
    from django.utils.functional import wraps

def get_occurrence_data_from_session(view):
    @wraps(view)
    def new_view(request, *args, **kwargs):
        occurrence_info = request.session.get('occurrence_info')
        if not occurrence_info:
            return HttpResponseRedirect(reverse('event-list'))

        event               = occurrence_info['event']
        valid_occurrences   = occurrence_info['valid_occurrences']
        invalid_occurrences = occurrence_info['invalid_occurrences']

        return view(request, event, valid_occurrences, invalid_occurrences,
                    *args, **kwargs)
    return new_view
