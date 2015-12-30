from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect


class NeverCacheMixin(object):
    """View mixin for disabling caching."""
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(request, *args, **kwargs)


class LoginRequiredMixin(object):
    """View mixin to require a logged in user."""
    @method_decorator(login_required(login_url=reverse_lazy('cas_login'),
                                     redirect_field_name=None))
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class CsrfProtectMixin(object):
    """View mixin to require CSRF protection."""
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(CsrfProtectMixin, self).dispatch(request, *args, **kwargs)


class CasResponseMixin(object):
    """
    View mixin for building CAS XML responses. Expects the view to
    implement ``get_context_data()`` and define ``response_class``.
    """
    content_type = 'text/xml'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def render_to_response(self, context):
        return self.response_class(context, content_type=self.content_type)
