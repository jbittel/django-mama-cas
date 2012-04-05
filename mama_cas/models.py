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


class TicketManager(models.Manager):
    def create_ticket(self, **kwargs):
        """
        Create a new ``Ticket`` and generate a sufficiently opaque ticket
        string to ensure the ticket is not guessable. Any provided arguments
        are passed on to the ``create()`` function. Return the newly created
        ``Ticket``.
        """
        ticket_str = "%s-%d-%s" % (self.model.TICKET_PREFIX, int(time.time()),
                                   get_random_string(length=TICKET_RAND_LEN))
        new_ticket = self.create(ticket=ticket_str, **kwargs)
        LOG.debug("Created ticket '%s'" % new_ticket.ticket)
        return new_ticket

    def validate_ticket(self, ticket, consume=True, service=None, renew=False):
        """
        Given a ticket string, validate the corresponding ``Ticket`` returning
        the ``Ticket`` if valid. If validation fails, return ``False``.

        If ``consume`` is True, the ticket will be consumed as part of the
        validation process.

        If ``service`` is provided and the ticket has a service attribute,
        the origin of the two services will be compared.

        if ``renew`` is provided, the validation will only succeed if the
        ticket was issued from the presentation of the user's primary
        credentials.
        """
        if not ticket:
            LOG.warn("No ticket string provided")
            return False

        if not TICKET_RE.match(ticket):
            LOG.warn("Invalid ticket string provided: %s" % ticket)
            return False

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            LOG.warn("Ticket '%s' does not exist" % ticket)
            return False

        if t.is_consumed():
            LOG.warn("Ticket '%s' has already been used" % ticket)
            return False
        if consume:
            t.consume()

        if t.is_expired():
            LOG.warn("Ticket '%s' has expired" % ticket)
            return False

        if service and hasattr(t, 'service'):
            if not same_origin(t.service, service):
                LOG.warn("Ticket '%s' for service '%s' is invalid for service '%s'" % (ticket, t.service, service))
                return False

        if renew:
            # TODO if renew is set, only validate if the ticket was issued
            #      from the presentation of the user's primary credentials
            pass

        LOG.info("Validated ticket '%s'" % ticket)
        return t

    def consume_ticket(self, ticket):
        """
        Given a ticket string, consume the corresponding ``Ticket``
        returning the ``Ticket`` if the consumption succeeds. If the
        ``Ticket`` could not be located, return ``False``.
        """
        if not ticket:
            LOG.info("No ticket string provided")
            return False

        if not TICKET_RE.match(ticket):
            LOG.warn("Invalid ticket string provided: %s" % ticket)
            return False

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            LOG.warn("Ticket '%s' does not exist" % ticket)
            return False

        t.consume()

        LOG.info("Consumed ticket '%s'" % ticket)
        return t

    def delete_invalid_tickets(self):
        """
        Iterate over all ``Ticket``s and delete all consumed or expired
        ``Ticket``s. Invalid tickets are no longer valid for future
        authentication attempts and can be safely deleted.
        """
        for ticket in self.all():
            if ticket.is_consumed() or ticket.is_expired():
                ticket.delete()

class Ticket(models.Model):
    """
    ``Ticket`` is an abstract base class implementing common methods
    and fields for the assorted ticket types. It should never be
    interacted with directly within the application.
    """
    ticket = models.CharField(max_length=255, unique=True)
    created_on = models.DateTimeField()
    consumed = models.DateTimeField(null=True)

    objects = TicketManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % unicode(self.ticket)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = now()
        super(Ticket, self).save(*args, **kwargs)

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

class LoginTicket(Ticket):
    """
    (3.5) A ``LoginTicket`` is provided by /login as a credential requestor
    and passed to /login as a credential acceptor to prevent replaying of
    credentials. A ``LoginTicket`` is created automatically when the /login
    form is displayed.
    """
    TICKET_PREFIX = u"LT"
    TICKET_EXPIRE = getattr(settings, 'CAS_LOGIN_TICKET_EXPIRE', 20)

class ServiceTicket(Ticket):
    """
    (3.1) A ``ServiceTicket`` is used by the client as a credential to
    obtain access to a service. It is obtained upon a client's presentation
    of credentials and a service identifier to /login.
    """
    TICKET_PREFIX = u"ST"
    TICKET_EXPIRE = getattr(settings, 'CAS_SERVICE_TICKET_EXPIRE', 5)

    service = models.CharField(max_length=255)
    granted_by_tgt = models.ForeignKey('TicketGrantingTicket')

class TicketGrantingTicket(Ticket):
    """
    (2.1 and 3.6) A ``TicketGrantingTicket`` is created when valid credentials
    are provided to /login as a credential acceptor. A corresponding
    ticket-granting cookie is created on the client's machine and can be
    presented in lieu of primary credentials to obtain ``ServiceTicket``s.
    """
    TICKET_PREFIX = u"TGC"
    TICKET_EXPIRE = getattr(settings, 'CAS_LOGIN_EXPIRE', 1440)

    username = models.CharField(max_length=255)
    client_ip = models.CharField(max_length=64)
    warn = models.BooleanField()
