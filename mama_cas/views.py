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
from mama_cas.forms import WarnForm
from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.utils import add_query_params
from mama_cas.mixins import NeverCache
from mama_cas.mixins import LoginRequired
from mama_cas.mixins import ValidateTicket
from mama_cas.mixins import CustomAttributes
from mama_cas.mixins import LogoutUser


LOG = logging.getLogger('mama_cas')


class LoginView(NeverCache, LogoutUser, FormView):
    """
    (2.1 and 2.2) Credential requestor and acceptor.

    This URI operates in two modes: a credential requestor when a GET request
    is received, and a credential acceptor for POST requests.
    """
    template_name = 'mama_cas/login.html'
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        """
        As a credential requestor, /login accepts up to three optional
        parameters:

        1. ``service``: the identifier of the application the client is
           accessing. In most cases this will be a URL.
        2. ``renew``: requires a client to present credentials regardless of
           any existing single sign-on session. If set, its value should be
           "true".
        3. ``gateway``: causes the client to not be prompted for credentials.
           If a single sign-on session already exists, the user will be logged
           in. Otherwise, the user is simply forwarded to the service, if
           specified. If set, its value should be "true".
        """
        service = request.GET.get('service')
        renew = request.GET.get('renew')
        gateway = request.GET.get('gateway')
        warned = request.GET.get('warned')

        if renew:
            LOG.debug("Renew request received by credential requestor")
            LogoutUser.logout_user(self, request)
            login = add_query_params(reverse('cas_login'), { 'service': service })
            LOG.debug("Redirecting to %s" % login)
            return redirect(login)
        elif gateway and service:
            LOG.debug("Gateway request received by credential requestor")
            if request.user.is_authenticated():
                if self.warn_user() and not warned:
                    return redirect(add_query_params(reverse('cas_warn'),
                                                     { 'service': service,
                                                       'gateway': gateway }))
                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=request.user)
                service = add_query_params(service, { 'ticket': st.ticket })
            LOG.debug("Redirecting to %s" % service)
            return redirect(service)
        elif request.user.is_authenticated():
            if service:
                LOG.debug("Service ticket request received by credential requestor")
                if self.warn_user() and not warned:
                    return redirect(add_query_params(reverse('cas_warn'),
                                                     { 'service': service }))
                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=request.user)
                service = add_query_params(service, { 'ticket': st.ticket })
                LOG.debug("Redirecting to %s" % service)
                return redirect(service)
            else:
                messages.success(request, _("You are logged in as %s") % request.user)
        return super(LoginView, self).get(request, *args, **kwargs)

    def warn_user(self):
        """
        Returns ``True`` if the ``warn`` parameter is set in the current
        session. Otherwise, returns ``False``.
        """
        return self.request.session.get('warn', False)

    def form_valid(self, form):
        """
        As a credential acceptor, /login takes two required parameters:

        1. ``username``: the username provided by the client
        2. ``password``: the password provided by the client

        If authentication is successful, the user is logged in which creates
        the single sign-on session. If a service is provided, a corresponding
        ``ServiceTicket`` is created, and the user is redirected to the
        service URL. If no service is provided, the user is redirected back
        to the login page with a message indicating a successful login.

        If authentication fails, the login form is redisplayed with an appropriate
        error message displayed indicating the reason for failure.

        The credential acceptor also accepts one optional parameter:

        1. ``warn``: causes user input to be required whenever an
           authentication attempt occurs within the single sign-on session.
        """
        auth.login(self.request, form.user)
        LOG.info("User logged in as '%s'" % self.request.user)

        if form.cleaned_data.get('warn'):
            self.request.session['warn'] = True

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

class WarnView(NeverCache, LoginRequired, FormView):
    """
    (2.2.1) Disable transparent authentication by displaying a page indicating
    that authentication is taking place. The user can then choose to continue
    or cancel the authentication attempt.
    """
    template_name = 'mama_cas/warn.html'
    form_class = WarnForm

    def form_valid(self, form):
        return redirect(add_query_params(reverse('cas_login'),
                                        { 'service': form.cleaned_data.get('service'),
                                          'gateway': form.cleaned_data.get('gateway'),
                                          'warned': 'true' }))

    def get_initial(self):
        initial = {}
        service = self.request.GET.get('service')
        gateway = self.request.GET.get('gateway')
        if service:
            initial['service'] = urlquote_plus(service)
        if gateway:
            initial['gateway'] = gateway
        return initial

    def get_context_data(self, **kwargs):
        kwargs['service'] = self.request.GET.get('service')
        return kwargs

class LogoutView(NeverCache, LogoutUser, View):
    """
    (2.3) End a client's single sign-on session.

    When this URI is accessed, any current single sign-on session is
    ended, requiring a new single sign-on session to be established
    for future authentication attempts.

    If ``url`` is specified, it will be displayed to the user as a recommended
    link to follow.
    """
    def get(self, request, *args, **kwargs):
        LOG.debug("Logout request received for user %s" % request.user)
        LogoutUser.logout_user(self, request)
        url = request.GET.get('url', None)
        if url:
            messages.success(request, _("The application has provided this link to follow: " \
                "<a href=\"%(url)s\">%(url)s</a>") % { 'url': url }, extra_tags='safe')
        return redirect(reverse('cas_login'))

class ValidateView(NeverCache, ValidateTicket, View):
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
        st, pgt, error = ValidateTicket.validate_service_ticket(self, request)
        if st:
            return HttpResponse(content="yes\n%s\n" % st.user.username,
                                content_type='text/plain')
        else:
            return HttpResponse(content="no\n\n", content_type='text/plain')

class ServiceValidateView(NeverCache, ValidateTicket, CustomAttributes, TemplateView):
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
        st, pgt, error = ValidateTicket.validate_service_ticket(self, request)
        attributes = CustomAttributes.get_custom_attributes(self, st)
        context = { 'ticket': st, 'pgt': pgt, 'error': error, 'attributes': attributes }
        return self.render_to_response(context, content_type='text/xml')

class ProxyValidateView(NeverCache, ValidateTicket, CustomAttributes, TemplateView):
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
            t, pgt, proxies, error = ValidateTicket.validate_proxy_ticket(self, request)
            attributes = CustomAttributes.get_custom_attributes(self, t)
        else:
            t, pgt, error = ValidateTicket.validate_service_ticket(self, request)
            proxies = None
            attributes = CustomAttributes.get_custom_attributes(self, t)

        context = { 'ticket': t, 'pgt': pgt, 'proxies': proxies, 'error': error,
                    'attributes': attributes }
        return self.render_to_response(context, content_type='text/xml')

class ProxyView(NeverCache, ValidateTicket, TemplateView):
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
        pt, error = ValidateTicket.validate_proxy_granting_ticket(self, request)
        context = { 'ticket': pt, 'error': error }
        return self.render_to_response(context, content_type='text/xml')
