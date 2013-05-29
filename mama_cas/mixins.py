import logging

from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import SiteProfileNotAvailable
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidTicketError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import InternalError
from mama_cas.exceptions import BadPGTError


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


class ValidateTicketMixin(object):
    """
    View mixin providing ticket validation methods.
    """
    def validate_service_ticket(self, request):
        """
        Given a ``request``, validate a service ticket string. On success, a
        triplet is returned containing the ``ServiceTicket`` and an optional
        ``ProxyGrantingTicket``, with no error. On error, a triplet is
        returned containing no ``ServiceTicket`` or ``ProxyGrantingTicket``,
        but with an ``Error`` describing what went wrong.
        """
        service = request.GET.get('service')
        ticket = request.GET.get('ticket')
        renew = request.GET.get('renew')
        pgturl = request.GET.get('pgtUrl')

        logger.debug("Service validation request received for %s" % ticket)
        try:
            st = ServiceTicket.objects.validate_ticket(ticket,
                                                       service=service,
                                                       renew=renew)
        except (InvalidRequestError, InvalidTicketError,
                InvalidServiceError, InternalError) as e:
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
        Given a ``request``, validate a proxy ticket string. On success, a
        4-tuple is returned containing the ``ProxyTicket``, an optional
        ``ProxyGrantingTicket`` and a list of all services that proxied
        authentication, with no error. On error, a 4-tuple is returned
        containing no ``ProxyTicket``, ``ProxyGrantingTicket`` or list of
        proxies, but with an ``Error`` describing what went wrong.
        """
        service = request.GET.get('service')
        ticket = request.GET.get('ticket')
        pgturl = request.GET.get('pgtUrl')

        logger.debug("Proxy validation request received for %s" % ticket)
        try:
            pt = ProxyTicket.objects.validate_ticket(ticket,
                                                     service=service)
        except (InvalidRequestError, InvalidTicketError,
                InvalidServiceError, InternalError) as e:
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
        Given a ``request``, validate a proxy granting ticket string. On
        success, an ordered pair is returned containing a ``ProxyTicket``,
        with no error. On error, an ordered pair is returned containing no
        ``ProxyTicket``, but with an ``Error`` describing what went wrong.
        """
        pgt = request.GET.get('pgt')
        target_service = request.GET.get('targetService')

        logger.debug("Proxy ticket request received for %s using %s" %
                     (target_service, pgt))
        try:
            pgt = ProxyGrantingTicket.objects.validate_ticket(pgt,
                                                              target_service)
        except (InvalidRequestError, BadPGTError,
                InvalidServiceError, InternalError) as e:
            logger.warning("%s %s" % (e.code, e))
            return None, e
        else:
            pt = ProxyTicket.objects.create_ticket(service=target_service,
                                                   user=pgt.user,
                                                   granted_by_pgt=pgt)
            return pt, None


class CustomAttributesMixin(object):
    """
    View mixin for including custom user attributes in a validation response.
    """
    def get_custom_attributes(self, ticket):
        """
        Given a ``ticket``, build a list of user attributes from the ``User``
        and/or user profile object to be returned along with a validation
        success. The attributes are defined using two settings variables:

        ``MAMA_CAS_USER_ATTRIBUTES``
            This is a list of name and ``User`` attribute pairs. The name can
            be any meaningful string, while the attribute must correspond with
            an attribute on the ``User`` object.

        ``MAMA_CAS_PROFILE_ATTRIBUTES``
            This is a list of name and user profile attribute pairs. The name
            can be any meaningful string, while the attribute must correspond
            with an attribute on the user profile object.

        One or both of the settings variables may be used, with all data
        returned as a single list. Ordering is not guaranteed.
        """
        if not ticket:
            return None
        user = ticket.user
        attributes = []

        user_attr_list = getattr(settings, 'MAMA_CAS_USER_ATTRIBUTES', {})
        for name, attr in user_attr_list.items():
            try:
                attribute = [name, getattr(user, attr)]
            except AttributeError:
                logger.error("User has no attribute named '%s'" % attr)
            else:
                attributes.append(attribute)

        try:
            profile = user.get_profile()
        except (ObjectDoesNotExist, SiteProfileNotAvailable, AttributeError):
            pass
        else:
            profile_attr_list = getattr(settings,
                                        'MAMA_CAS_PROFILE_ATTRIBUTES', {})
            for name, attr in profile_attr_list.items():
                try:
                    attribute = [name, getattr(profile, attr)]
                except AttributeError:
                    logger.error("Profile has no attribute named '%s'" % attr)
                else:
                    attributes.append(attribute)

        return attributes


class LogoutUserMixin(object):
    """
    View mixin for logging a user out of a single sign-on session.
    """
    def logout_user(self, request):
        """
        Given a ``request``, end a single sign-on session for the current
        user. This process occurs in two steps:

        1. Consume all ``Ticket``s created for the user to ensure none of
           them continue to be valid outside of the active session.

        2. Call logout() to end the active session and completely remove all
           existing session data for the current request.
        """
        if request.user.is_authenticated():
            ServiceTicket.objects.consume_tickets(request.user)
            ProxyTicket.objects.consume_tickets(request.user)
            ProxyGrantingTicket.objects.consume_tickets(request.user)

            logger.info("Single sign-on session ended for %s" % request.user)
            logout(request)
            messages.success(request,
                             _("You have been successfully logged out"))
