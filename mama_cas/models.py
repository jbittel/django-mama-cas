from datetime import timedelta
import time
import logging
import re

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from django.utils.http import same_origin


LOG = logging.getLogger(__name__)

TICKET_RAND_LEN = getattr(settings, 'CAS_TICKET_RAND_LEN', 32)
TICKET_RE = re.compile("^[A-Z]{2,3}-[0-9]{10,}-[a-zA-Z0-9]{%d}$" % TICKET_RAND_LEN)


class Ticket(models.Model):
    """
    ``Ticket`` is an abstract base class implementing common methods
    and fields for the assorted ticket types. It should never be
    interacted with directly within the application.
    """
    ticket = models.CharField(max_length=255, unique=True)
    created_on = models.DateTimeField()
    consumed = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % unicode(self.ticket)

    def __init__(self, *args, **kwargs):
        super(Ticket, self).__init__(*args, **kwargs)
        if not self.ticket:
            self.generate(prefix=self.TICKET_PREFIX)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = now()
        super(Ticket, self).save(*args, **kwargs)

    def generate(self, prefix=''):
        """
        Create a sufficiently opaque ticket string using random data
        to ensure a ``Ticket`` is not guessable. An optional prefix string
        can be provided that is prepended to the ticket string.
        """
        self.ticket = "%s-%d-%s" % (prefix, int(time.time()), get_random_string(length=TICKET_RAND_LEN))

    def consume(self):
        """
        A ``Ticket`` is consumed by populating the ``consumed`` field with
        the current datetime. A consumed ``Ticket`` is no longer valid for
        any future authentication attempts.
        """
        self.consumed = now()
        self.save()

    def is_consumed(self):
        """
        Check a ``Ticket``s consumed state. Return ``True`` if the ticket is
        consumed, and ``False`` otherwise.
        """
        if self.consumed:
            return True
        return False

    def is_expired(self):
        """
        Check a ``Ticket``s expired state. Return ``True`` if the ticket is
        expired, and ``False`` otherwise.
        """
        if self.created_on + timedelta(minutes=self.TICKET_EXPIRE) <= now():
            return True
        return False

class LoginTicketManager(models.Manager):
    def create_ticket(self):
        """
        Create a new ``LoginTicket``, returning the newly created
        ``LoginTicket``.
        """
        lt = self.create()
        LOG.debug("Created login ticket '%s'" % lt.ticket)
        return lt

    def validate_ticket(self, ticket):
        """
        Validate a ``LoginTicket`` by checking both its consumed and
        expired states, returning the ``LoginTicket``.

        If the ``LoginTicket`` is not consumed, consume it as part of
        the validation process.

        If the ``LoginTicket`` does not exist or is invalid, return
        ``False``.
        """
        if not ticket:
            LOG.warn("No login ticket string provided")
            return False

        if not TICKET_RE.match(ticket):
            LOG.warn("Invalid login ticket string provided: %s" % ticket)
            return False

        try:
            lt = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            LOG.warn("Login ticket '%s' does not exist" % ticket)
            return False

        if lt.is_consumed():
            LOG.warn("Login ticket '%s' has already been used" % ticket)
            return False
        lt.consume()

        if lt.is_expired():
            LOG.warn("Login ticket '%s' has expired" % ticket)
            return False

        LOG.info("Validated login ticket '%s'" % ticket)
        return lt

    def delete_invalid_tickets(self):
        """
        Iterate over all ``LoginTicket``s and delete all consumed or expired
        tickets. Invalid tickets are no longer valid for future authentication
        attempts and can be safely deleted.
        """
        for ticket in self.all():
            if ticket.is_consumed() or ticket.is_expired():
                ticket.delete()

class LoginTicket(Ticket):
    """
    (3.5) A ``LoginTicket`` is provided by /login as a credential requestor
    and passed to /login as a credential acceptor to prevent replaying of
    credentials. A ``LoginTicket`` is created automatically when the /login
    form is displayed.

    You shouldn't need to interact directly with this model. Instead,
    ``LoginTicketManager`` provides methods for creating, validating
    and deleting expired ``LoginTicket``s.
    """
    TICKET_PREFIX = u"LT"
    TICKET_EXPIRE = getattr(settings, 'CAS_LOGIN_TICKET_EXPIRE', 20)

    objects = LoginTicketManager()

class ServiceTicketManager(models.Manager):
    def create_ticket(self, service, tgt):
        """
        Create a new ``ServiceTicket`` and create a relationship to the
        ``TicketGrantingTicket`` that authorized this ``ServiceTicket``.
        Return the new ``ServiceTicket``.
        """
        st = self.create(service=service, granted_by_tgt=tgt)
        LOG.debug("Created ticket '%s' from ticket '%s' for service '%s'" % (st.ticket, tgt.ticket, service))
        return st

    def validate_ticket(self, ticket, service, renew):
        """
        Validate a ``ServiceTicket`` by checking both its consumed and
        expired states, returning the ``ServiceTicket``.

        If the ``ServiceTicket`` is not consumed, consume it as part of
        the validation process.

        If the ``ServiceTicket`` does not exist or is invalid, return
        ``False``.
        """
        # TODO if renew is set, only validate if the service ticket was issued
        #      from the presentation of the user's primary credentials

        if not ticket:
            LOG.warn("No service ticket string provided")
            return False

        if not service:
            LOG.warn("No service provided")
            return False

        if not TICKET_RE.match(ticket):
            LOG.warn("Invalid service ticket string provided: %s" % ticket)
            return False

        try:
            # Perform a select_related() lookup here so we have access to the
            # TGT fields in the view without incurring additional DB lookups
            st = self.select_related().get(service=service, ticket=ticket)
        except self.model.DoesNotExist:
            LOG.warn("Service ticket '%s' does not exist" % ticket)
            return False

        if st.is_consumed():
            LOG.warn("Service ticket '%s' has already been used" % ticket)
            return False
        st.consume()

        if st.is_expired():
            LOG.warn("Service ticket '%s' is expired" % ticket)
            return False

        if not same_origin(st.service, service):
            LOG.warn("Service ticket '%s' for service '%s' is invalid for service '%s'" % (ticket, st.service, service))
            return False

        LOG.info("Validated service ticket '%s' for service '%s'" % (ticket, service))
        return st

class ServiceTicket(Ticket):
    """
    (3.1) A ``ServiceTicket`` is used by the client as a credential to
    obtain access to a service. It is obtained upon a client's presentation
    of credentials and a service identifier to /login.

    You shouldn't need to interact directly with this model. Instead,
    ``ServiceTicketManager`` provides methods for creating and validating
    ``ServiceTicket``s.
    """
    TICKET_PREFIX = u"ST"
    TICKET_EXPIRE = getattr(settings, 'CAS_SERVICE_TICKET_EXPIRE', 5)

    service = models.CharField(max_length=255)
    granted_by_tgt = models.ForeignKey('TicketGrantingTicket')

    objects = ServiceTicketManager()

class TicketGrantingTicketManager(models.Manager):
    def create_ticket(self, username, ip):
        """
        Create a new ``TicketGrantingTicket``, returning the new
        ``TicketGrantingTicket.
        """
        tgt = self.create(username=username, client_ip=ip)
        LOG.debug("Created ticket granting ticket %s" % tgt.ticket)
        return tgt

    def validate_ticket(self, tgc):
        """
        Validate a ``TicketGrantingTicket`` by checking both its
        consumed and expired states, returning the ``TicketGrantingTicket``.

        If the provided ticket granting cookie string is invalid,
        return ``False``.
        """
        if not tgc:
            LOG.warn("No ticket granting cookie string provided")
            return False

        if not TICKET_RE.match(tgc):
            LOG.warn("Invalid ticket granting cookie string provided: %s" % tgc)
            return False

        try:
            tgt = self.get(ticket=tgc)
        except self.model.DoesNotExist:
            LOG.warn("Ticket granting ticket '%s' does not exist" % tgc)
            return False

        if tgt.is_consumed():
            LOG.warn("Ticket granting ticket '%s' has been used up" % tgc)
            return False

        if tgt.is_expired():
            LOG.warn("Ticket granting ticket '%s' is expired" % tgc)
            return False

        LOG.info("Validated ticket granting ticket '%s'" % tgc)
        return tgt

    def consume_ticket(self, tgc):
        """
        Given a ticket-granting cookie string, consume the matching
        ``TicketGrantingTicket`` to render it invalid for future
        authentication attempts, returning the ``TicketGrantingTicket``.

        If the provided ticket granting cookie string is invalid,
        return ``False``.
        """
        if not tgc:
            LOG.warn("No ticket granting cookie string provided")
            return False

        if not TICKET_RE.match(tgc):
            LOG.warn("Invalid ticket granting ticket string provided: %s" % tgc)
            return False

        try:
            tgt = self.get(ticket=tgc)
        except self.model.DoesNotExist:
            LOG.warn("Ticket granting ticket '%s' does not exist" % tgc)
            return False

        tgt.consume()

        LOG.info("Consumed ticket granting ticket '%s'" % tgt.ticket)
        return tgt

    def delete_invalid_tickets(self):
        """
        Iterate over all ``TicketGrantingTicket``s and delete all consumed or
        expired tickets. Invalid tickets are no longer valid for future
        authentication attempts and can be safely deleted.
        """
        for ticket in self.all():
            if ticket.is_consumed() or ticket.is_expired():
                ticket.delete()

class TicketGrantingTicket(Ticket):
    """
    (2.1 and 3.6) A ``TicketGrantingTicket`` is created when valid credentials
    are provided to /login as a credential acceptor. A corresponding
    ticket-granting cookie is created on the client's machine and can be
    presented in lieu of primary credentials to obtain ``ServiceTicket``s.

    You shouldn't need to interact directly with this model. Instead,
    ``TicketGrantingTicketManager`` provides methods for creating, validating
    and deleting expired ``TicketGrantingTicket``s.
    """
    TICKET_PREFIX = u"TGC"
    TICKET_EXPIRE = getattr(settings, 'CAS_LOGIN_EXPIRE', 1440)

    username = models.CharField(max_length=255)
    client_ip = models.CharField(max_length=64)
    warn = models.BooleanField()

    objects = TicketGrantingTicketManager()
