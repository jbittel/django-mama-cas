import logging

from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidTicketError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import InternalError
from mama_cas.exceptions import BadPGTError


LOG = logging.getLogger('mama_cas')


class NeverCacheMixin(object):
    """
    View mixin that disables caching
    """
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(request, *args, **kwargs)

class TicketValidateMixin(object):
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

        LOG.debug("Service validation request received for %s" % ticket)
        try:
            st = ServiceTicket.objects.validate_ticket(ticket,
                                                       service=service,
                                                       renew=renew)
        except (InvalidRequestError, InvalidTicketError,
                InvalidServiceError, InternalError) as e:
            LOG.warn("%s %s" % (e.code, e))
            return None, None, e
        else:
            if pgturl:
                LOG.debug("Proxy-granting ticket request received for %s" % pgturl)
                pgt = ProxyGrantingTicket.objects.create_ticket(pgturl,
                                                                user=st.user,
                                                                granted_by_st=st)
            else:
                pgt = None
            return st, pgt, None

    def validate_proxy_ticket(self, request):
        """
        Given a ``request``, validate a proxy ticket string. On success, a
        4-tuple is returned containing the ``ProxyTicket``, a list of all
        services that proxied authentication and an optional
        ``ProxyGrantingTicket``, with no error. On error, a triplet is
        returned containing no ``ProxyTicket`` or ``ProxyGrantingTicket``,
        but with an ``Error`` describing what went wrong.
        """
        service = request.GET.get('service')
        ticket = request.GET.get('ticket')
        pgturl = request.GET.get('pgtUrl')

        LOG.debug("Proxy validation request received for %s" % ticket)
        try:
            pt = ProxyTicket.objects.validate_ticket(ticket,
                                                     service=service)
        except (InvalidRequestError, InvalidTicketError,
                InvalidServiceError, InternalError) as e:
            LOG.warn("%s %s" % (e.code, e))
            return None, None, None, e
        else:
            # Build a list of all services that proxied authentication,
            # in reverse order of which they were traversed
            proxies = [pt.service]
            prior_pt = pt.granted_by_pgt.granted_by_pt
            while prior_pt:
                proxies.append(prior_pt.service)
                prior_pt = pt.granted_by_pgt.granted_by_pt

            if pgturl:
                LOG.debug("Proxy-granting ticket request received for %s" % pgturl)
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

        LOG.debug("Proxy ticket request received")
        try:
            pgt = ProxyGrantingTicket.objects.validate_ticket(pgt,
                                                              target_service)
        except (InvalidRequestError, BadPGTError, InternalError) as e:
            LOG.warn("%s %s" % (e.code, e))
            return None, e
        else:
            pt = ProxyTicket.objects.create_ticket(service=target_service,
                                                   user=pgt.user,
                                                   granted_by_pgt=pgt)
            return pt, None
