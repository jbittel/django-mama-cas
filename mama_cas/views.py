import logging

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote_plus
from django.core.urlresolvers import reverse
from django.contrib import messages

from mama_cas.forms import LoginForm
from mama_cas.models import ServiceTicket
from mama_cas.models import TicketGrantingTicket
from mama_cas.utils import add_query_params
from mama_cas.utils import get_client_ip


LOG = logging.getLogger('mama_cas')


def login(request, form_class=LoginForm,
          template_name='mama_cas/login.html'):
    """
    (2.1 and 2.2) Credential requestor and acceptor.

    This URI operates in two modes: a credential requestor when a GET request
    is received, and a credential acceptor for POST requests.

    As a credential requestor, it takes up to three optional parameters:

    1. service - the identifier of the application the client is accessing. In
       most cases this will be a URL.
    2. renew - if set, a client must present credentials regardless of any
       existing single sign-on session. If set, its value should be "true".
    3. gateway - if set, the client will not be prompted for credentials. If
       set, its value should be "true".

    As a credential acceptor, it takes three required parameters:

    1. username - the username provided by the client
    2. password - the password provided by the client
    3. lt - a ``LoginTicket`` created as part of the login form

    If authentication is successful, a ``TicketGrantingTicket`` is created and
    the user is redirected back to the login page so that a corresponding
    ``ServiceTicket`` may be created.

    If authentication fails, the login form is redisplayed with an appropriate
    error message displayed indicating the reason for failure.
    """
    if request.POST:
        form = form_class(request.POST.copy())

        if form.is_valid():
            # TODO implement warn
            service = form.cleaned_data.get('service')
            username = form.cleaned_data.get('username')
            tgt = TicketGrantingTicket.objects.create_ticket(username=username,
                                                             client_ip=get_client_ip(request))
            url = add_query_params(reverse('cas_login'), {'service': service})
            response = HttpResponseRedirect(url)
            response.set_signed_cookie('tgc', tgt.ticket)
            return response
    else:
        service = request.GET.get('service')
        renew = request.GET.get('renew')
        gateway = request.GET.get('gateway')

        tgc = request.get_signed_cookie('tgc', False)
        tgt = TicketGrantingTicket.objects.validate_ticket(tgc, consume=False)

        if renew:
            LOG.debug("Renew request received by credential requestor")
            TicketGrantingTicket.objects.consume_ticket(tgc)
        elif gateway and service:
            LOG.debug("Gateway request received by credential requestor")
            if tgt:
                st = ServiceTicket.objects.create_ticket(service=service, granted_by_tgt=tgt)
                service = add_query_params(service, {'ticket': st.ticket})
            return HttpResponseRedirect(service)
        else:
            if tgt:
                LOG.debug("Service ticket request received by credential requestor")
                LOG.debug("Ticket granting ticket '%s' provided" % tgt.ticket)
                if service:
                    LOG.debug("Creating service ticket for '%s'" % service)
                    st = ServiceTicket.objects.create_ticket(service=service, granted_by_tgt=tgt)
                    service = add_query_params(service, {'ticket': st.ticket})
                    return HttpResponseRedirect(service)
                else:
                    messages.success(request, "You are logged in as %s" % tgt.username)
                    LOG.info("User logged in as '%s' using ticket '%s'" % (tgt.username, tgt.ticket))
            else:
                LOG.debug("No ticket granting ticket provided")

        if service:
            form = form_class(initial={'service': urlquote_plus(service)})
        else:
            form = form_class()

    return render(request, template_name,
                  {'form': form})

def logout(request,
           template_name='mama_cas/logout.html'):
    """
    (2.3) End a client's single sign-on CAS session.

    When this URI is accessed, any existing ``TicketGrantingTicket`` is
    consumed, rendering it invalid for future authentication attempts and
    requiring a new single sign-on session to be established.

    If a URL is specified, it will be displayed on the page as a suggested
    link to follow.
    """
    url = request.GET.get('url', None)
    tgc = request.get_signed_cookie('tgc', False)
    if tgc:
        TicketGrantingTicket.objects.consume_ticket(tgc)
    response = render(request, template_name, {'url': url})
    response.delete_cookie('tgc')

    return response

def validate(request):
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
    service = request.GET.get('service', None)
    ticket = request.GET.get('ticket', None)
    renew = request.GET.get('renew', None)

    if service and ticket:
        st = ServiceTicket.objects.validate_ticket(ticket, service=service, renew=renew)
        if st:
            return HttpResponse(content="yes\n%s\n" % st.granted_by_tgt.username,
                                content_type='text/plain')

    return HttpResponse(content="no\n\n",
                        content_type='text/plain')

def service_validate(request):
    """
    (2.5) Check the validity of a service ticket. [CAS 2.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)

def proxy_validate(request):
    """
    (2.6) Check the validity of a service ticket, and additionally
    validate proxy tickets. [CAS 2.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)

def proxy(request):
    """
    (2.7) Provide proxy tickets to services that have acquired proxy-
    granting tickets. [CAS 2.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)
