from datetime import timedelta
import time

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from django.utils.http import same_origin


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
        self.ticket = "%s-%d-%s" % (prefix, int(time.time()), get_random_string(length=32))

    def consume(self):
        """
        A ``Ticket`` is consumed by populating the ``consumed`` field with
        the current datetime. A consumed ``Ticket`` is no longer valid for
        any future authentication attempts.
        """
        self.consumed = now()

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
        Create a new ``LoginTicket`` and save the ``LoginTicket`` to the database.
        Return the newly created ``LoginTicket``.
        """
        lt = LoginTicket()
        lt.save()
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
        Returns the new ``ServiceTicket``.
        """
        st = ServiceTicket(service=service)
        st.granted_by_tgt = tgt
        st.save()
        return st

    def validate_ticket(self, service, ticket, renew):
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
        try:
            st = self.select_related().get(service=service, ticket=ticket)
        except self.model.DoesNotExist:
            return False

        if st.is_consumed():
            return False
        st.consume()
        st.save()

        if st.is_expired() or not same_origin(st.service, service):
            return False

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
    def create_ticket(self, username, host):
        """
        Create a new ``TicketGrantingTicket``, returning the new
        ``TicketGrantingTicket.
        """
        tgt = TicketGrantingTicket(username=username, host=host)
        tgt.save()
        return tgt

    def validate_ticket(self, tgc):
        """
        Validate a ``TicketGrantingTicket`` by checking both its
        consumed and expired states, returning the ``TicketGrantingTicket``.

        If the provided ticket granting cookie string is invalid,
        return ``False``.
        """
        if not tgc:
            return False

        try:
            tgt = TicketGrantingTicket.objects.get(ticket=tgc)
        except self.model.DoesNotExist:
            return False

        if tgt.is_consumed() or tgt.is_expired():
            return False

        return tgt

    def consume_ticket(self, tgc):
        """
        Consume a ``TicketGrantingTicket`` to render it invalid for
        future authentication attempts, returning the ``TicketGrantingTicket``.

        If the provided ticket granting cookie string is invalid,
        return ``False``.
        """
        if not tgc:
            return False

        try:
            tgt = TicketGrantingTicket.objects.get(ticket=tgc)
        except self.model.DoesNotExist:
            return False

        tgt.consume()
        tgt.save()

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
    are provided to /login as a credential acceptor. A corresponding cookie
    is created on the client's machine and can be presented in lieu of primary
    credentials to obtain ``ServiceTicket``s.

    You shouldn't need to interact directly with this model. Instead,
    ``TicketGrantingTicketManager`` provides methods for creating, validating
    and deleting expired ``TicketGrantingTicket``s.
    """
    TICKET_PREFIX = u"TGC"
    TICKET_EXPIRE = getattr(settings, 'CAS_LOGIN_EXPIRE', 1440)

    username = models.CharField(max_length=255)
    host = models.CharField(max_length=64)

    objects = TicketGrantingTicketManager()
