import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.exceptions import InvalidTicketSpec
from mama_cas.exceptions import ValidationError


logger = logging.getLogger(__name__)


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


class ValidateTicketMixin(object):
    """View mixin providing ticket validation methods."""
    def validate_service_ticket(self, service, ticket, pgturl,
                                renew=False, require_https=False):
        """
        Validate a service ticket string. Return a triplet containing
        a ``ServiceTicket`` and an optional ``ProxyGrantingTicket``,
        or a ``ValidationError`` subclass if ticket validation failed.
        """
        logger.debug("Service validation request received for %s" % ticket)
        # Check for proxy tickets passed to /serviceValidate
        if ticket and ticket.startswith(ProxyTicket.TICKET_PREFIX):
            e = InvalidTicketSpec('Proxy tickets cannot be validated'
                                  ' with /serviceValidate')
            logger.warning("%s %s" % (e.code, e))
            return None, None, e

        try:
            st = ServiceTicket.objects.validate_ticket(ticket, service,
                    renew=renew, require_https=require_https)
        except ValidationError as e:
            logger.warning("%s %s" % (e.code, e))
            return None, None, e
        else:
            if pgturl:
                logger.debug("Proxy-granting ticket request received for %s" %
                             pgturl)
                pgt = ProxyGrantingTicket.objects.create_ticket(pgturl,
                        user=st.user, granted_by_st=st)
            else:
                pgt = None
            return st, pgt, None

    def validate_proxy_ticket(self, service, ticket, pgturl):
        """
        Validate a proxy ticket string. Return a 4-tuple containing a
        ``ProxyTicket``, an optional ``ProxyGrantingTicket`` and a list
        of proxies through which authentication proceeded, or a
        ``ValidationError`` subclass if ticket validation failed.
        """
        logger.debug("Proxy validation request received for %s" % ticket)
        try:
            pt = ProxyTicket.objects.validate_ticket(ticket, service)
        except ValidationError as e:
            logger.warning("%s %s" % (e.code, e))
            return None, None, None, e
        else:
            # Build a list of all services that proxied authentication,
            # in reverse order of which they were traversed
            proxies = [pt.service]
            prior_pt = pt.granted_by_pgt.granted_by_pt
            while prior_pt:
                proxies.append(prior_pt.service)
                prior_pt = prior_pt.granted_by_pgt.granted_by_pt

            if pgturl:
                logger.debug("Proxy-granting ticket request received for %s" %
                             pgturl)
                pgt = ProxyGrantingTicket.objects.create_ticket(pgturl,
                                                                user=pt.user,
                                                                granted_by_pt=pt)
            else:
                pgt = None
            return pt, pgt, proxies, None

    def validate_proxy_granting_ticket(self, pgt, target_service):
        """
        Validate a proxy granting ticket string. Return an ordered
        pair containing a ``ProxyTicket``, or a ``ValidationError``
        subclass if ticket validation failed.
        """
        logger.debug("Proxy ticket request received for %s using %s" %
                     (target_service, pgt))
        try:
            pgt = ProxyGrantingTicket.objects.validate_ticket(pgt,
                                                              target_service)
        except ValidationError as e:
            logger.warning("%s %s" % (e.code, e))
            return None, e
        else:
            pt = ProxyTicket.objects.create_ticket(service=target_service,
                                                   user=pgt.user,
                                                   granted_by_pgt=pgt)
            return pt, None


class CustomAttributesMixin(object):
    """
    View mixin for including user attributes in a validation response.
    """
    def get_attributes(self, user, service):
        """
        Build a dictionary of user attributes from a set of callbacks
        specified with ``MAMA_CAS_ATTRIBUTE_CALLBACKS``.
        """
        attributes = {}

        callbacks = getattr(settings, 'MAMA_CAS_ATTRIBUTE_CALLBACKS', ())
        for path in callbacks:
            callback = import_string(path)
            attributes.update(callback(user, service))

        return attributes


class LogoutUserMixin(object):
    """
    View mixin for logging a user out of a single sign-on session.
    """
    def logout_user(self, request):
        """
        End a single sign-on session for the current user. This process
        occurs in three steps:

        1. Consume all valid tickets created for the user.

        2. (Optional) Send single logout requests to services.

        3. Call logout() to end the session and purge all session data.
        """
        logger.debug("Logout request received for %s" % request.user)
        if request.user.is_authenticated():
            ServiceTicket.objects.consume_tickets(request.user)
            ProxyTicket.objects.consume_tickets(request.user)
            ProxyGrantingTicket.objects.consume_tickets(request.user)

            if getattr(settings, 'MAMA_CAS_ENABLE_SINGLE_SIGN_OUT', False):
                ServiceTicket.objects.request_sign_out(request.user)

            logger.info("Single sign-on session ended for %s" % request.user)
            logout(request)
            msg = _("You have been successfully logged out")
            messages.success(request, msg)
