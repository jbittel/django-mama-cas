from datetime import timedelta
import time
import logging
import re

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import same_origin
from django.contrib.auth.models import User


LOG = logging.getLogger('mama_cas')

TICKET_RAND_LEN = getattr(settings, 'CAS_TICKET_RAND_LEN', 32)
TICKET_RE = re.compile("^[A-Z]{2}-[0-9]{10,}-[a-zA-Z0-9]{%d}$" % TICKET_RAND_LEN)


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
        now = timezone.now()

        new_ticket = self.create(ticket=ticket_str, created_on=now, **kwargs)
        LOG.debug("Created ticket '%s'" % new_ticket.ticket)
        return new_ticket

    def validate_ticket(self, ticket, service=None, renew=False):
        """
        Given a ticket string, validate the corresponding ``Ticket`` returning
        the ``Ticket`` if valid. If validation fails, return ``False``.

        If ``consume`` is True, the ticket will be consumed as part of the
        validation process.

        If ``service`` is provided and the ticket has a service attribute,
        the origin of the two services will be compared. Validation will only
        succeed if the service origins match.

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
        t.consume()

        if t.is_expired():
            LOG.warn("Ticket '%s' has expired" % ticket)
            return False

        if service and hasattr(t, 'service'):
            if not same_origin(t.service, service):
                LOG.warn("Ticket '%s' for service '%s' is invalid for service '%s'" % (ticket, t.service, service))
                return False

        if renew and not t.is_primary():
            LOG.warn("Ticket '%s' was not issued via primary credentials" % ticket)
            return False

        LOG.info("Validated ticket '%s'" % ticket)
        return t

    def delete_invalid_tickets(self):
        """
        Iterate over all ``Ticket``s and delete all consumed or expired
        ``Ticket``s. Invalid tickets are no longer valid for future
        authentication attempts and can be safely deleted.

        A custom management command is provided that executes this method
        on all applicable models by running ``manage.py cleanupcas``. It
        is recommended that you run this command on a regular basis to
        prevent invalid tickets from causing storage or performance issues.
        """
        for ticket in self.all():
            if ticket.is_consumed() or ticket.is_expired():
                ticket.delete()

class Ticket(models.Model):
    """
    ``Ticket`` is an abstract base class implementing common methods
    and fields for the assorted ticket types. It should never be
    interacted with directly within the application.

    It is recommended that you do not interact directly with this model
    or its inheritors. Instead, the provided manager contains methods
    for creating, validating, consuming and deleting invalid ``Ticket``s.
    """
    ticket = models.CharField(max_length=255, unique=True)
    created_on = models.DateTimeField()
    consumed = models.DateTimeField(null=True)

    objects = TicketManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % unicode(self.ticket)

    def consume(self):
        """
        A ``Ticket`` is consumed by populating the ``consumed`` field with
        the current datetime. A consumed ``Ticket`` is no longer valid for
        any future authentication attempts.
        """
        self.consumed = timezone.now()
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
        if self.created_on + timedelta(minutes=self.TICKET_EXPIRE) <= timezone.now():
            return True
        return False

    def is_primary(self):
        """
        Check the credential origin for a ``Ticket``. If the ticket was
        issued from the presentation of the user's primary credentials,
        return ``True``, otherwise return ``False``.
        """
        if self.primary:
            return True
        return False

class ServiceTicket(Ticket):
    """
    (3.1) A ``ServiceTicket`` is used by the client as a credential to
    obtain access to a service. It is obtained upon a client's presentation
    of credentials and a service identifier to /login.
    """
    TICKET_PREFIX = u"ST"
    TICKET_EXPIRE = getattr(settings, 'CAS_SERVICE_TICKET_EXPIRE', 5)

    service = models.CharField(max_length=255)
    user = models.ForeignKey(User)
    primary = models.BooleanField()

    class Meta:
        verbose_name = "service ticket"
        verbose_name_plural = "service tickets"
