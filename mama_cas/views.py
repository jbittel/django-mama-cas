import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus
from django.utils.translation import ugettext as _
from django.views.generic import FormView
from django.views.generic import TemplateView
from django.views.generic import View

from mama_cas.forms import LoginForm
from mama_cas.forms import WarnForm
from mama_cas.mixins import CustomAttributesMixin
from mama_cas.mixins import LoginRequiredMixin
from mama_cas.mixins import LogoutUserMixin
from mama_cas.mixins import NeverCacheMixin
from mama_cas.mixins import ValidateTicketMixin
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket
from mama_cas.utils import add_query_params
from mama_cas.utils import is_valid_service_url


logger = logging.getLogger(__name__)


class LoginView(NeverCacheMixin, LogoutUserMixin, FormView):
    """
    (2.1 and 2.2) Credential requestor and acceptor.

    This view operates as a credential requestor when a GET request
    is received, and a credential acceptor for POST requests.
    """
    template_name = 'mama_cas/login.html'
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        """
        (2.1) As a credential requestor, /login accepts three optional
        parameters:

        1. ``service``: the identifier of the application the client is
           accessing. We assume this identifier to be a URL.
        2. ``renew``: requires a client to present credentials
           regardless of any existing single sign-on session. If set,
           its value should be ``true``.
        3. ``gateway``: causes the client to not be prompted for
           credentials. If a single sign-on session already exists, the
           user will be logged in. Otherwise, the user is simply
           forwarded to the service, if specified. If set, its value
           should be ``true``.
        """
        service = request.GET.get('service')
        renew = request.GET.get('renew')
        gateway = request.GET.get('gateway')
        warned = request.GET.get('warned')

        if renew:
            logger.debug("Renew request received by credential requestor")
            self.logout_user(request)
            login_url = add_query_params(reverse('cas_login'),
                                         {'service': service})
            logger.debug("Redirecting to %s" % login_url)
            return redirect(login_url)
        elif gateway and service:
            logger.debug("Gateway request received by credential requestor")
            if request.user.is_authenticated():
                if self.warn_user() and not warned:
                    warn_url = add_query_params(reverse('cas_warn'),
                                                {'service': service,
                                                 'gateway': gateway})
                    return redirect(warn_url)

                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=request.user)
                service_url = add_query_params(service, {'ticket': st.ticket})
            else:
                service_url = service
            logger.debug("Redirecting to %s" % service_url)
            return redirect(service_url)
        elif request.user.is_authenticated():
            if service:
                logger.debug("Service ticket request received "
                             "by credential requestor")
                if self.warn_user() and not warned:
                    warn_url = add_query_params(reverse('cas_warn'),
                                                {'service': service})
                    return redirect(warn_url)

                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=request.user)
                service_url = add_query_params(service, {'ticket': st.ticket})
                logger.debug("Redirecting to %s" % service_url)
                return redirect(service_url)
            else:
                msg = _("You are logged in as %s") % request.user
                messages.success(request, msg)
        return super(LoginView, self).get(request, *args, **kwargs)

    def warn_user(self):
        """
        Returns ``True`` if the ``warn`` parameter is set in the
        current session. Otherwise, returns ``False``.
        """
        return self.request.session.get('warn', False)

    def get_form_kwargs(self):
        """
        Set the form's label suffix to an empty string. Django 1.6
        defaults to a ':' suffix for a label_tag.
        """
        form_kwargs = super(LoginView, self).get_form_kwargs()
        form_kwargs['label_suffix'] = ''
        return form_kwargs

    def form_valid(self, form):
        """
        (2.2) As a credential acceptor, /login requires two parameters:

        1. ``username``: the username provided by the client
        2. ``password``: the password provided by the client

        If authentication is successful, the single sign-on session is
        created. If a service is provided, a ``ServiceTicket`` is
        created and the client is redirected to the service URL with
        the ``ServiceTicket`` included. If no service is provided, the
        login page is redisplayed with a message indicating a
        successful login.

        If authentication fails, the login form is redisplayed with an
        error message describing the reason for failure.

        The credential acceptor accepts one optional parameter:

        1. ``warn``: causes the user to be prompted when successive
           authentication attempts occur within the single sign-on
           session.
        """
        login(self.request, form.user)
        logger.info("Single sign-on session started for %s" % form.user)

        if form.cleaned_data.get('warn'):
            self.request.session['warn'] = True

        service = form.cleaned_data.get('service')
        if service:
            st = ServiceTicket.objects.create_ticket(service=service,
                                                     user=self.request.user,
                                                     primary=True)
            service = add_query_params(service, {'ticket': st.ticket})
            logger.debug("Redirecting to %s" % service)
            return redirect(service)
        return redirect(reverse('cas_login'))

    def get_initial(self):
        service = self.request.GET.get('service')
        if service:
            return {'service': urlquote_plus(service)}


class WarnView(NeverCacheMixin, LoginRequiredMixin, FormView):
    """
    (2.2.1) Disables transparent authentication by informing the user
    that service authentication is taking place. The user can choose
    to continue or cancel the authentication attempt.
    """
    template_name = 'mama_cas/warn.html'
    form_class = WarnForm

    def form_valid(self, form):
        service = form.cleaned_data.get('service')
        gateway = form.cleaned_data.get('gateway')
        return redirect(add_query_params(reverse('cas_login'),
                                         {'service': service,
                                          'gateway': gateway,
                                          'warned': 'true'}))

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


class LogoutView(NeverCacheMixin, LogoutUserMixin, View):
    """
    (2.3) End a client's single sign-on session.

    When this view is accessed, an existing single sign-on session is
    ended, requiring a new single sign-on session to be established
    for future authentication attempts.

    If ``url`` is specified, by default it will be displayed to the
    user as a recommended link to follow. This behavior can be altered
    by setting ``MAMA_CAS_FOLLOW_LOGOUT_URL`` to ``True``, which will
    redirect the client to the specified URL.
    """
    def get(self, request, *args, **kwargs):
        logger.debug("Logout request received for %s" % request.user)
        self.logout_user(request)
        url = request.GET.get('url')
        if url and is_valid_service_url(url):
            if getattr(settings, 'MAMA_CAS_FOLLOW_LOGOUT_URL', False):
                return redirect(url)
            msg = _("The application provided this link to follow: %s") % url
            messages.success(request, msg)
        return redirect(reverse('cas_login'))


class ValidateView(NeverCacheMixin, ValidateTicketMixin, View):
    """
    (2.4) Check the validity of a service ticket. [CAS 1.0]

    When both ``service`` and ``ticket`` are provided, this view
    responds with a ``ServiceTicket`` validation success or failure.
    Whether or not the validation succeeds, the ``ServiceTicket`` is
    consumed, rendering it invalid for future authentication attempts.

    If ``renew`` is specified, validation will only succeed if the
    ``ServiceTicket`` was issued from the presentation of the user's
    primary credentials, not from an existing single sign-on session.
    """
    def get(self, request, *args, **kwargs):
        st, pgt, error = self.validate_service_ticket(request)
        if st:
            return HttpResponse(content="yes\n%s\n" % st.user.username,
                                content_type='text/plain')
        else:
            return HttpResponse(content="no\n\n", content_type='text/plain')


class ServiceValidateView(NeverCacheMixin, ValidateTicketMixin,
                          CustomAttributesMixin, TemplateView):
    """
    (2.5) Check the validity of a service ticket. [CAS 2.0]

    When both ``service`` and ``ticket`` are provided, this view
    responds with an XML-fragment response indicating a
    ``ServiceTicket`` validation success or failure. Whether or not
    validation succeeds, the ticket is consumed, rendering it invalid
    for future authentication attempts.

    If ``renew`` is specified, validation will only succeed if the
    ``ServiceTicket`` was issued from the presentation of the user's
    primary credentials, not from an existing single sign-on session.

    If ``pgtUrl`` is specified, the response will include a
    ``ProxyGrantingTicket`` if the proxy callback URL has a valid SSL
    certificate and responds with a successful HTTP status code.
    """
    content_type = 'text/xml'
    template_name = 'mama_cas/validate.xml'

    def get(self, request, *args, **kwargs):
        st, pgt, error = self.validate_service_ticket(request)
        attributes = self.get_custom_attributes(st)
        context = {'ticket': st, 'pgt': pgt, 'error': error,
                   'attributes': attributes}
        return self.render_to_response(context)


class ProxyValidateView(NeverCacheMixin, ValidateTicketMixin,
                        CustomAttributesMixin, TemplateView):
    """
    (2.6) Perform the same validation tasks as ServiceValidateView and
    additionally validate proxy tickets. [CAS 2.0]

    When both ``service`` and ``ticket`` are provided, this view
    responds with an XML-fragment response indicating a ``ProxyTicket``
    or ``ServiceTicket`` validation success or failure. Whether or not
    validation succeeds, the ticket is consumed, rendering it invalid
    for future authentication attempts.

    If ``renew`` is specified, validation will only succeed if the
    ``ServiceTicket`` was issued from the presentation of the user's
    primary credentials, not from an existing single sign-on session.

    If ``pgtUrl`` is specified, the response will include a
    ``ProxyGrantingTicket`` if the proxy callback URL has a valid SSL
    certificate and responds with a successful HTTP status code.
    """
    content_type = 'text/xml'
    template_name = 'mama_cas/validate.xml'

    def get(self, request, *args, **kwargs):
        ticket = request.GET.get('ticket')
        if not ticket or ticket.startswith(ProxyTicket.TICKET_PREFIX):
            # If no ticket parameter is present, attempt to validate it
            # anyway so the appropriate error is raised
            t, pgt, proxies, error = self.validate_proxy_ticket(request)
            attributes = self.get_custom_attributes(t)
        else:
            t, pgt, error = self.validate_service_ticket(request)
            proxies = None
            attributes = self.get_custom_attributes(t)

        context = {'ticket': t, 'pgt': pgt, 'proxies': proxies,
                   'error': error, 'attributes': attributes}
        return self.render_to_response(context)


class ProxyView(NeverCacheMixin, ValidateTicketMixin, TemplateView):
    """
    (2.7) Provide proxy tickets to services that have acquired proxy-
    granting tickets. [CAS 2.0]

    When both ``pgt`` and ``targetService`` are specified, this view
    responds with an XML-fragment response indicating a
    ``ProxyGrantingTicket`` validation success or failure. If
    validation succeeds, a ``ProxyTicket`` will be created and included
    in the response.
    """
    content_type = 'text/xml'
    template_name = 'mama_cas/proxy.xml'

    def get(self, request, *args, **kwargs):
        pt, error = self.validate_proxy_granting_ticket(request)
        context = {'ticket': pt, 'error': error}
        return self.render_to_response(context)
