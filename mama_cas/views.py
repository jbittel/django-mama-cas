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
from django.template.loader import get_template
from django.template import Context

from mama_cas.forms import LoginForm
from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.utils import add_query_params
from mama_cas.mixins import NeverCacheMixin
from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidTicketError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import InternalError
from mama_cas.exceptions import BadPGTError


LOG = logging.getLogger('mama_cas')


class LoginView(NeverCacheMixin, FormView):
    """
    (2.1 and 2.2) Credential requestor and acceptor.

    This URI operates in two modes: a credential requestor when a GET request
    is received, and a credential acceptor for POST requests.

    """
    template_name = 'mama_cas/login.html'
    form_class = LoginForm

    def get(self, *args, **kwargs):
        """
        As a credential requestor, /login takes up to three optional parameters:

        1. service - the identifier of the application the client is accessing.
           In most cases this will be a URL.
        2. renew - if set, a client must present credentials regardless of any
           existing single sign-on session. If set, its value should be "true".
        3. gateway - if set, the client will not be prompted for credentials. If
           set, its value should be "true".

        """
        service = self.request.GET.get('service')
        renew = self.request.GET.get('renew')
        gateway = self.request.GET.get('gateway')

        if renew:
            LOG.debug("Renew request received by credential requestor")
            auth.logout(self.request)
            login = add_query_params(reverse('cas_login'), { 'service': service })
            LOG.debug("Redirecting to %s" % login)
            return redirect(login)
        elif gateway and service:
            LOG.debug("Gateway request received by credential requestor")
            if self.request.user.is_authenticated():
                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=self.request.user)
                service = add_query_params(service, { 'ticket': st.ticket })
            LOG.debug("Redirecting to %s" % service)
            return redirect(service)
        elif self.request.user.is_authenticated():
            if service:
                LOG.debug("Service ticket request received by credential requestor")
                st = ServiceTicket.objects.create_ticket(service=service,
                                                         user=self.request.user)
                service = add_query_params(service, { 'ticket': st.ticket })
                LOG.debug("Redirecting to %s" % service)
                return redirect(service)
            else:
                messages.success(self.request, "You are logged in as %s" % self.request.user)
        return super(LoginView, self).get(*args, **kwargs)

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

    def get(self, *args, **kwargs):
        LOG.debug("Logout request received for user '%s'" % self.request.user)
        if self.request.user.is_authenticated():
            ProxyGrantingTicket.objects.consume_tickets(self.request.user)
            auth.logout(self.request)
        messages.success(self.request, "You have been successfully logged out.")
        url = self.request.GET.get('url', None)
        if url:
            messages.success(self.request, "The application has provided this link to follow: " \
                "<a href=\"%s\">%s</a>" % (url, url), extra_tags='safe')
        return redirect(reverse('cas_login'))

class ValidateView(NeverCacheMixin, View):
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
    def get(self, *args, **kwargs):
        service = self.request.GET.get('service')
        ticket = self.request.GET.get('ticket')
        renew = self.request.GET.get('renew')

        LOG.debug("Validation request received for %s" % ticket)
        try:
            st = ServiceTicket.objects.validate_ticket(ticket, service=service, renew=renew)
        except (InvalidRequestError, InvalidTicketError, InvalidServiceError, InternalError) as e:
            LOG.warn("%s %s" % (e.code, e))
            return self.validation_failure()
        else:
            return self.validation_success(st.user.username)

    def validation_success(self, username):
        return HttpResponse(content="yes\n%s\n" % username, content_type='text/plain')

    def validation_failure(self):
        return HttpResponse(content="no\n\n", content_type='text/plain')

class ServiceValidateView(NeverCacheMixin, View):
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
    template_success = 'mama_cas/validate_success.xml'
    template_failure = 'mama_cas/validate_failure.xml'

    def get(self, *args, **kwargs):
        service = self.request.GET.get('service')
        ticket = self.request.GET.get('ticket')
        renew = self.request.GET.get('renew')
        pgturl = self.request.GET.get('pgtUrl')

        LOG.debug("Service validation request received for %s" % ticket)
        try:
            st = ServiceTicket.objects.validate_ticket(ticket, service=service, renew=renew)
        except (InvalidRequestError, InvalidTicketError, InvalidServiceError, InternalError) as e:
            LOG.warn("%s %s" % (e.code, e))
            return self.validation_failure(e.code, e.msg)
        else:
            if pgturl:
                LOG.debug("Proxy-granting ticket request received for %s" % pgturl)
                pgt = ProxyGrantingTicket.objects.create_ticket(pgturl, user=st.user,
                                                                granted_by_st=st)
            else:
                pgt = None
            return self.validation_success(st.user.username, pgt)

    def validation_success(self, username, pgt=None):
        template = get_template(self.template_success)
        content = template.render(Context({ 'username': username, 'pgt': pgt }))
        return HttpResponse(content=content, content_type='text/xml')

    def validation_failure(self, error_code, error_msg):
        template = get_template(self.template_failure)
        content = template.render(Context({ 'error_code': error_code, 'error_msg': error_msg }))
        return HttpResponse(content=content, content_type='text/xml')

class ProxyValidateView(ServiceValidateView):
    """
    (2.6) Check the validity of a service ticket, and additionally
    validate proxy tickets. [CAS 2.0]
    """
    # TODO validate proxy tickets
    pass

class ProxyView(NeverCacheMixin, View):
    """
    (2.7) Provide proxy tickets to services that have acquired proxy-
    granting tickets. [CAS 2.0]

    When both ``pgt`` and ``targetService`` are specified, this URI responds
    with an XML-fragment response indicating a ``ProxyGrantingTicket``
    validation success or failure. If validation succeeds, a ``ProxyTicket``
    will be created and included in the response.
    """
    template_success = 'mama_cas/proxy_success.xml'
    template_failure = 'mama_cas/proxy_failure.xml'

    def get(self, *args, **kwargs):
        pgt = self.request.GET.get('pgt')
        target_service = self.request.GET.get('targetService')

        LOG.debug("Proxy ticket request received")
        try:
            pgt = ProxyGrantingTicket.objects.validate_ticket(pgt, target_service)
        except (InvalidRequestError, BadPGTError, InternalError) as e:
            LOG.warn("%s %s" % (e.code, e))
            return self.validation_failure(e.code, e)
        else:
            pt = ProxyTicket.objects.create_ticket(service=target_service,
                                                   user=pgt.user,
                                                   granted_by_pgt=pgt)
            return self.validation_success(pt)

    def validation_success(self, pt):
        template = get_template(self.template_success)
        content = template.render(Context({ 'pt': pt }))
        return HttpResponse(content=content, content_type='text/xml')

    def validation_failure(self, error_code, error_msg):
        template = get_template(self.template_failure)
        content = template.render(Context({ 'error_code': error_code, 'error_msg': error_msg }))
        return HttpResponse(content=content, content_type='text/xml')
