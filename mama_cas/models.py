from datetime import datetime
from datetime import timedelta
import hashlib
import os
import time

from django.db import models
from django.conf import settings
from django.utils.timezone import utc


class Ticket(models.Model):
    ticket = models.CharField(max_length=255, unique=True)
    created_on = models.DateTimeField()
    consumed = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % unicode(self.ticket)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = datetime.now()
        super(Ticket, self).save(*args, **kwargs)

    def generate(self, prefix=''):
        """
        Create a sufficiently opaque ticket string using random data
        to ensure a ``Ticket`` is not guessable. An optional prefix string
        can be provided that is prepended to the ticket string.
        """
        self.ticket = "%s-%d-%s" % (prefix, int(time.time()), hashlib.sha1(os.urandom(512)).hexdigest())

    def consume(self):
        """
        A ``Ticket`` is consumed by when it is used by populating the
        ``consumed`` field with the current datetime. A consumed ``Ticket``
        is no longer valid for any future authentication attempts.
        """
        self.consumed = datetime.now()

    def is_consumed(self):
        if self.consumed:
            return True
        return False

    def is_expired(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        if self.created_on + timedelta(minutes=1) < now:
            return True
        return False

class LoginTicketManager(models.Manager):
    """
    Create a new ``LoginTicket``, populate ``ticket`` with a new ticket
    string and save the ``LoginTicket`` to the database. Return the
    generated ticket ID.

    """
    def create_ticket(self):
        lt = LoginTicket()
        lt.generate(prefix=LoginTicket.TICKET_PREFIX)
        lt.save()
        return lt.ticket

class LoginTicket(Ticket):
    """
    A string that is saved to the DB and passed to /login as a credential
    acceptor to prevent replaying of credentials. A ``LoginTicket`` is
    created automatically when the /login form is displayed.


    You shouldn't need to interact directly with this model. Instead,
    ``LoginTicketManager`` provides methods for creating, validating
    and deleting expired ``LoginTicket``s.

    """
    TICKET_PREFIX = u"LT"

    objects = LoginTicketManager()

class ServiceTicketManager(models.Manager):
    def create_ticket(self, service, username):
        st = ServiceTicket(service=service, username=username)
        st.generate(prefix=ServiceTicket.TICKET_PREFIX)
        st.consume()
        st.save()
        return st.ticket

    def validate_ticket(self, service, ticket, renew):
        # TODO if renew is set, only validate if the service ticket was issued
        # from the presentation of the user's primary credentials
        service_ticket = ServiceTicket.objects.get(service=service, ticket=ticket)
        if service_ticket:
            return service_ticket.username
        return None

class ServiceTicket(Ticket):
    TICKET_PREFIX = u"ST"

    service = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    objects = ServiceTicketManager()

class TicketGrantingTicketManager(models.Manager):
    def create_ticket(self, username):
        tgt = TicketGrantingTicket(username=username)
        tgt.generate(prefix=TicketGrantingTicket.TICKET_PREFIX)
        tgt.consume()
        tgt.save()
        return tgt.ticket

class TicketGrantingTicket(Ticket):
    TICKET_PREFIX = u"TGC"

    username = models.CharField(max_length=255)

    objects = TicketGrantingTicketManager()
