# myapp/decorators.py

from django.http import HttpResponseForbidden

def director_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'director':
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You do not have permission to view this page.")
    return _wrapped_view
