import logging

from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.views.generic import FormView
from django.views.generic import TemplateView
from django.views.generic import View
from django.contrib import auth
from django.utils.translation import ugettext as _

from mama_cas.forms import LoginForm
from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.utils import add_query_params
from mama_cas.mixins import NeverCacheMixin
from mama_cas.mixins import TicketValidateMixin


LOG = logging.getLogger('mama_cas')


class LoginView(NeverCacheMixin, FormView):
    """
    (2.1 and 2.2) Credential requestor and acceptor.

    This URI operates in two modes: a credential requestor when a GET request
    is received, and a credential acceptor for POST requests.
    """
    template_name = 'mama_cas/login.html'
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        """
        As a credential requestor, /login takes up to three optional parameters:

        1. service - the identifier of the application the client is accessing.
           In most cases this will be a URL.
        2. renew - if set, a client must present credentials regardless of any
           existing single sign-on session. If set, its value should be "true".
        3. gateway - if set, the client will not be prompted for credentials. If
           set, its value should be "true".
        """
        service = request.GET.get('service')
        renew = request.GET.get('renew')
        gateway = request.GET.get('gateway')

        if renew:
            LOG.debug("Renew request received by credential requestor")
            auth.logout(request)
            login = add_query_params(reverse('cas_login'), { 'service': service })
            LOG.debug("Redirecting to %s" % login)
            return redirect(login)
        elif gateway and service:
            LOG.debug("Gateway request received by credential requestor")
            if request.user.is_authenticated():
                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=request.user)
                service = add_query_params(service, { 'ticket': st.ticket })
            LOG.debug("Redirecting to %s" % service)
            return redirect(service)
        elif request.user.is_authenticated():
            if service:
                LOG.debug("Service ticket request received by credential requestor")
                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=request.user)
                service = add_query_params(service, { 'ticket': st.ticket })
                LOG.debug("Redirecting to %s" % service)
                return redirect(service)
            else:
                messages.success(request, _("You are logged in as %s") % request.user)
        return super(LoginView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        """
        As a credential acceptor, /login takes two required parameters:

        1. username - the username provided by the client
        2. password - the password provided by the client

        If authentication is successful, the user is logged in which creates
        the single sign-on session. If a service is provided, a corresponding
        ``ServiceTicket`` is created, and the user is redirected to the
        service URL. If no service is provided, the user is redirected back
        to the login page with a message indicating a successful login.

        If authentication fails, the login form is redisplayed with an appropriate
        error message displayed indicating the reason for failure.
        """
        auth.login(self.request, form.user)
        LOG.info("User logged in as '%s'" % self.request.user)
        service = form.cleaned_data.get('service')
        if service:
            st = ServiceTicket.objects.create_ticket(service=service,
                                                     user=self.request.user,
                                                     primary=True)
            service = add_query_params(service, { 'ticket': st.ticket })
            LOG.debug("Redirecting to %s" % service)
            return redirect(service)
        return redirect(reverse('cas_login'))

    def get_initial(self):
        service = self.request.GET.get('service')
        if service:
            return { 'service': urlquote_plus(service) }

class LogoutView(NeverCacheMixin, TemplateView):
    """
    (2.3) End a client's single sign-on CAS session.

    When this URI is accessed, any current single sign-on session is
    ended, requiring a new single sign-on session to be established
    for future authentication attempts.

    If a URL is specified, it will be displayed on the page as a suggested
    link to follow.
    """
    template_name = 'mama_cas/login.html'

    def get(self, request, *args, **kwargs):
        LOG.debug("Logout request received for user '%s'" % request.user)
        if request.user.is_authenticated():
            ProxyGrantingTicket.objects.consume_tickets(request.user)
            auth.logout(request)
        messages.success(request, _("You have been successfully logged out."))
        url = request.GET.get('url', None)
        if url:
            messages.success(request, _("The application has provided this link to follow: " \
                "<a href=\"%(url)s\">%(url)s</a>") % { 'url': url }, extra_tags='safe')
        return redirect(reverse('cas_login'))

class ValidateView(NeverCacheMixin, TicketValidateMixin, View):
    """
    (2.4) Check the validity of a service ticket. [CAS 1.0]

    When both ``service`` and ``ticket`` are provided, this URI responds with
    a ``ServiceTicket`` validation success or failure. Whether or not the
    validation succeeds, the ``ServiceTicket`` is consumed, rendering it
    invalid for future authentication attempts.

    If ``renew`` is specified, validation will only succeed if the
    ``ServiceTicket`` was issued from the presentation of the user's primary
    credentials (i.e. not from an existing single sign-on session).
    """
    def get(self, request, *args, **kwargs):
        ticket, pgt, error = TicketValidateMixin.validate_service_ticket(self, request)
        if ticket:
            return HttpResponse(content="yes\n%s\n" % ticket.user.username,
                                content_type='text/plain')
        else:
            return HttpResponse(content="no\n\n", content_type='text/plain')

class ServiceValidateView(NeverCacheMixin, TicketValidateMixin, TemplateView):
    """
    (2.5) Check the validity of a service ticket. [CAS 2.0]

    When both ``service`` and ``ticket`` are provided, this URI responds with
    an XML-fragment response indicating a ``ServiceTicket`` validation success
    or failure. Whether or not the validation succeeds, the ``ServiceTicket``
    is consumed, rendering it invalid for future authentication attempts.

    If ``renew`` is specified, validation will only succeed if the
    ``ServiceTicket`` was issued from the presentation of the user's primary
    credentials (i.e. not from an existing single sign-on session).

    If ``pgtUrl`` is specified, the response will also include a
    ``ProxyGrantingTicket`` if the proxy callback URL has a valid SSL
    certificate and responds with a successful HTTP status code.
    """
    template_name = 'mama_cas/validate.xml'

    def get(self, request, *args, **kwargs):
        ticket, pgt, error = TicketValidateMixin.validate_service_ticket(self, request)
        context = self.get_context_data(**kwargs)
        context.update({ 'ticket': ticket, 'pgt': pgt, 'error': error })
        return self.render_to_response(context, content_type='text/xml')

class ProxyValidateView(NeverCacheMixin, TicketValidateMixin, TemplateView):
    """
    (2.6) Check the validity of a service ticket, and additionally
    validate proxy tickets. [CAS 2.0]

    When both ``service`` and ``ticket`` are provided, this URI responds with
    an XML-fragment response indicating a ``ProxyTicket`` or ``ServiceTicket``
    validation success or failure. Whether or not the validation succeeds, the
    ``ProxyTicket`` or ``ServiceTicket`` is consumed, rendering it invalid for
    future authentication attempts.

    If ``renew`` is specified, validation will only succeed if the
    ``ServiceTicket`` was issued from the presentation of the user's primary
    credentials (i.e. not from an existing single sign-on session).

    If ``pgtUrl`` is specified, the response will also include a
    ``ProxyGrantingTicket`` if the proxy callback URL has a valid SSL
    certificate and responds with a successful HTTP status code.
    """
    template_name = 'mama_cas/validate.xml'

    def get(self, request, *args, **kwargs):
        ticket = request.GET.get('ticket')
        if not ticket or ticket.startswith(ProxyTicket.TICKET_PREFIX):
            # If no ticket parameter is present, attempt to validate it anyway
            # so the appropriate error is raised
            ticket, pgt, error = TicketValidateMixin.validate_proxy_ticket(self, request)
        else:
            ticket, pgt, error = TicketValidateMixin.validate_service_ticket(self, request)

        context = self.get_context_data(**kwargs)
        context.update({ 'ticket': ticket, 'pgt': pgt, 'error': error })
        return self.render_to_response(context, content_type='text/xml')

class ProxyView(NeverCacheMixin, TicketValidateMixin, TemplateView):
    """
    (2.7) Provide proxy tickets to services that have acquired proxy-
    granting tickets. [CAS 2.0]

    When both ``pgt`` and ``targetService`` are specified, this URI responds
    with an XML-fragment response indicating a ``ProxyGrantingTicket``
    validation success or failure. If validation succeeds, a ``ProxyTicket``
    will be created and included in the response.
    """
    template_name = 'mama_cas/proxy.xml'

    def get(self, request, *args, **kwargs):
        ticket, error = TicketValidateMixin.validate_proxy_granting_ticket(self, request)
        context = self.get_context_data(**kwargs)
        context.update({ 'ticket': ticket, 'error': error })
        return self.render_to_response(context, content_type='text/xml')
