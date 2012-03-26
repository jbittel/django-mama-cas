from datetime import datetime
import hashlib
import os
import time

from django.db import models


class Ticket(models.Model):
    ticket = models.CharField(max_length=255, unique=True)
    created_on = models.DateTimeField()
    consumed = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s' % unicode(ticket)

    def save(self, *args, **kwargs):
        self.created_on = datetime.now()
        super(Ticket, self).save(*args, **kwargs)

    def generate_ticket_id(self, prefix=''):
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

class LoginTicketManager(models.Manager):
    """
    Create a new ``LoginTicket``, populate ``ticket`` with a new ticket
    id and save the ``LoginTicket`` to the database. Return the generated
    ticket ID.
    """
    def create_login_ticket(self):
        lt = LoginTicket()
        lt.generate_ticket_id(prefix='LT')
        lt.save()

        return lt.ticket

class LoginTicket(Ticket):
    objects = LoginTicketManager()


class ServiceTicket(Ticket):
    service = models.CharField(max_length=256)
    username = models.CharField(max_length=256)
