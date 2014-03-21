import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import get_callable
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from mama_cas.compat import SiteProfileNotAvailable
from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.exceptions import InvalidTicket
from mama_cas.exceptions import ValidationError


logger = logging.getLogger(__name__)


class NeverCacheMixin(object):
    """
    View mixin for disabling caching.
    """
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(request, *args, **kwargs)


class LoginRequiredMixin(object):
    """
    View mixin to require a logged in user.
    """
    @method_decorator(login_required(login_url=reverse_lazy('cas_login'),
                                     redirect_field_name=None))
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class CasResponseMixin(object):
    """
    View mixin for building CAS XML responses. Expects the view to
    implement get_context_data() and define response_class.
    """
    content_type = 'text/xml'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def render_to_response(self, context):
        return self.response_class(context, content_type=self.content_type)


class ValidateTicketMixin(object):
    """
    View mixin providing ticket validation methods.
    """
    def validate_service_ticket(self, request):
        """
        Validate a service ticket string. Return a triplet containing
        a ``ServiceTicket`` and an optional ``ProxyGrantingTicket``,
        or a ``ValidationError`` subclass if ticket validation failed.
        """
        service = request.GET.get('service')
        ticket = request.GET.get('ticket')
        renew = bool(request.GET.get('renew'))
        pgturl = request.GET.get('pgtUrl')

        logger.debug("Service validation request received for %s" % ticket)

        # Check for proxy tickets passed to /serviceValidate
        if ticket and ticket.startswith(ProxyTicket.TICKET_PREFIX):
            e = InvalidTicket('Proxy tickets cannot be validated'
                              ' with /serviceValidate')
            logger.warning("%s %s" % (e.code, e))
            return None, None, e

        try:
            st = ServiceTicket.objects.validate_ticket(ticket, service,
                                                       renew=renew)
        except ValidationError as e:
            logger.warning("%s %s" % (e.code, e))
            return None, None, e
        else:
            if pgturl:
                logger.debug("Proxy-granting ticket request received for %s" %
                             pgturl)
                pgt = ProxyGrantingTicket.objects.create_ticket(pgturl,
                                                                user=st.user,
                                                                granted_by_st=st)
            else:
                pgt = None
            return st, pgt, None

    def validate_proxy_ticket(self, request):
        """
        Validate a proxy ticket string. Return a 4-tuple containing a
        ``ProxyTicket``, an optional ``ProxyGrantingTicket`` and a list
        of proxies through which authentication proceeded, or a
        ``ValidationError`` subclass if ticket validation failed.
        """
        service = request.GET.get('service')
        ticket = request.GET.get('ticket')
        pgturl = request.GET.get('pgtUrl')

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

    def validate_proxy_granting_ticket(self, request):
        """
        Validate a proxy granting ticket string. Return an ordered
        pair containing a ``ProxyTicket``, or a ``ValidationError``
        subclass if ticket validation failed.
        """
        pgt = request.GET.get('pgt')
        target_service = request.GET.get('targetService')

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
    def get_custom_attributes(self, ticket):
        """
        Build a list of user attributes from the ``User`` object, the
        user profile object or a custom callback callable. Attributes
        are specified with one or more settings:

        ``MAMA_CAS_USER_ATTRIBUTES``
            A dict of name and ``User`` attribute values. The name can
            be any meaningful string, while the attribute must
            correspond with an attribute on the ``User`` object.

        ``MAMA_CAS_PROFILE_ATTRIBUTES``
            A dict of name and user profile attribute values. The name
            can be any meaningful string, while the attribute must
            correspond with an attribute on the user profile object.

        ``MAMA_CAS_ATTRIBUTES_CALLBACK``
            A string representation of a custom callable that returns
            a dict containing attributes. The callable is provided a
            single argument of the ``User``.

        All attributes are returned as a single dictionary.
        """
        if not ticket:
            return None
        user = ticket.user
        attributes = {}

        user_attr_list = getattr(settings, 'MAMA_CAS_USER_ATTRIBUTES', {})
        for name, attr in user_attr_list.items():
            try:
                attributes[name] = getattr(user, attr)
            except AttributeError:
                logger.error("User has no attribute named '%s'" % attr)

        try:
            profile = user.get_profile()
        except (ObjectDoesNotExist, SiteProfileNotAvailable, AttributeError):
            pass
        else:
            profile_attr_list = getattr(settings,
                                        'MAMA_CAS_PROFILE_ATTRIBUTES', {})
            for name, attr in profile_attr_list.items():
                try:
                    attributes[name] = getattr(profile, attr)
                except AttributeError:
                    logger.error("Profile has no attribute named '%s'" % attr)

        callback_str = getattr(settings, 'MAMA_CAS_ATTRIBUTES_CALLBACK', None)
        if callback_str is not None:
            callback = get_callable(callback_str)
            attributes.update(callback(user))

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

        2. (Optional) Send single sign-out requests to services.

        3. Call logout() to end the session and purge all session data.
        """
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
