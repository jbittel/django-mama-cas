from __future__ import unicode_literals

from datetime import timedelta
import logging
import os
import re
import requests
import time

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.http import same_origin
from django.utils.translation import ugettext_lazy as _
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:  # Django version < 1.5
    from django.contrib.auth.models import User

from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidTicketError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import InternalError
from mama_cas.exceptions import BadPGTError
from mama_cas.utils import add_query_params
from mama_cas.utils import is_scheme_https
from mama_cas.utils import clean_service_url
from mama_cas.utils import is_valid_service_url


logger = logging.getLogger(__name__)


class TicketManager(models.Manager):
    def create_ticket(self, ticket=None, **kwargs):
        """
        Create a new ``Ticket`` with the appropriate default values. Any
        provided arguments are passed on to the ``create()`` function.
        Return the newly created ``Ticket``.
        """
        if not ticket:
            ticket = self.create_ticket_str()
        if 'service' in kwargs:
            kwargs['service'] = clean_service_url(kwargs['service'])
        t = self.create(ticket=ticket, created=timezone.now(), **kwargs)
        logger.debug("Created %s %s" % (t.name, t.ticket))
        return t

    def create_ticket_str(self, prefix=None):
        """
        Generate a sufficiently opaque ticket string to ensure the ticket is
        not guessable. If a prefix is provided, prepend it to the string.
        """
        if not prefix:
            prefix = self.model.TICKET_PREFIX
        return "%s-%d-%s" % (prefix, int(time.time()),
                             get_random_string(length=self.model.TICKET_RAND_LEN))

    def validate_ticket(self, ticket, service=None, renew=False):
        """
        Given a ticket string, validate the corresponding ``Ticket``
        returning the ``Ticket`` if valid. If validation fails, raise
        an appropriate error.

        If ``service`` is provided and the ticket has a service attribute,
        the origin of the two services will be compared. Validation will only
        succeed if the service origins match.

        If ``renew`` is provided, the validation will only succeed if the
        ticket was issued from the presentation of the user's primary
        credentials.
        """
        if not ticket:
            raise InvalidRequestError("No ticket string provided")

        if not self.model.TICKET_RE.match(ticket):
            raise InvalidTicketError("Ticket string %s is invalid" % ticket)

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            raise InvalidTicketError("Ticket %s does not exist" % ticket)

        if t.is_consumed():
            raise InvalidTicketError("%s %s has already been used" %
                                     (t.name, ticket))
        t.consume()

        if t.is_expired():
            raise InvalidTicketError("%s %s has expired" % (t.name, ticket))

        if not service:
            raise InvalidRequestError("No service identifier provided")

        if not is_valid_service_url(service):
            raise InvalidServiceError("Service %s is not a valid %s URL" %
                                      (service, t.name))

        if not same_origin(t.service, service):
            raise InvalidServiceError("%s %s for service %s is invalid for service %s" %
                                      (t.name, ticket, t.service, service))

        if renew and not t.is_primary():
            raise InvalidTicketError("%s %s was not issued via primary credentials" %
                                     (t.name, ticket))

        logger.debug("Validated %s %s" % (t.name, ticket))
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

    def consume_tickets(self, user):
        """
        Iterate over all ``Ticket``s for a specified user and consume all
        tickets if they are not already consumed or expired. This is used
        when the user logs out to ensure all tickets issued for this user
        are no longer valid for future authentication attempts.
        """
        for ticket in self.filter(user=user):
            if not ticket.is_consumed() and not ticket.is_expired():
                ticket.consume()


@python_2_unicode_compatible
class Ticket(models.Model):
    """
    ``Ticket`` is an abstract base class implementing common methods
    and fields for the assorted ticket types.

    It is recommended that you do not interact directly with this model
    or its inheritors. Instead, the provided manager contains methods
    for creating, validating, consuming and deleting invalid ``Ticket``s.
    """
    TICKET_EXPIRE = getattr(settings, 'MAMA_CAS_TICKET_EXPIRE', 5)
    TICKET_RAND_LEN = getattr(settings, 'MAMA_CAS_TICKET_RAND_LEN', 32)
    TICKET_RE = re.compile("^[A-Z]{2,3}-[0-9]{10,}-[a-zA-Z0-9]{%d}$" % TICKET_RAND_LEN)

    ticket = models.CharField(_('ticket'), max_length=255, unique=True)
    user = models.ForeignKey(User, verbose_name=_('user'))
    created = models.DateTimeField(_('created'))
    consumed = models.DateTimeField(_('consumed'), null=True)

    objects = TicketManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.ticket

    @property
    def name(self):
        return self._meta.verbose_name

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
        if self.created + timedelta(minutes=self.TICKET_EXPIRE) <= timezone.now():
            return True
        return False


class ServiceTicket(Ticket):
    """
    (3.1) A ``ServiceTicket`` is used by the client as a credential to
    obtain access to a service. It is obtained upon a client's presentation
    of credentials and a service identifier to /login.
    """
    TICKET_PREFIX = 'ST'

    service = models.CharField(_('service'), max_length=255)
    primary = models.BooleanField(_('primary'), default=False)

    class Meta:
        verbose_name = _('service ticket')
        verbose_name_plural = _('service tickets')

    def is_primary(self):
        """
        Check the credential origin for a ``ServiceTicket``. If the ticket was
        issued from the presentation of the user's primary credentials,
        return ``True``, otherwise return ``False``.
        """
        if self.primary:
            return True
        return False


class ProxyTicket(Ticket):
    """
    (3.2) A ``ProxyTicket`` is used by a service as a credential to obtain
    access to a back-end service on behalf of a client. It is obtained upon
    a service's presentation of a ``ProxyGrantingTicket`` and a service
    identifier.
    """
    TICKET_PREFIX = 'PT'

    service = models.CharField(_('service'), max_length=255)
    granted_by_pgt = models.ForeignKey('ProxyGrantingTicket',
                                       verbose_name=_('granted by proxy-granting ticket'))

    class Meta:
        verbose_name = _('proxy ticket')
        verbose_name_plural = _('proxy tickets')


class ProxyGrantingTicketManager(TicketManager):
    def create_ticket(self, pgturl, validate=True, **kwargs):
        """
        When a ``pgtUrl`` parameter is provided to ``/serviceValidate`` or
        ``/proxyValidate``, attempt to create a new ``ProxyGrantingTicket``.
        Start by creating the necessary ticket strings and then validate the
        callback URL. If validation succeeds, create and return the
        ``ProxyGrantingTicket``. If validation fails, return ``None``.

        If ``validate`` is set to False, ``pgtUrl`` validation is skipped.
        This is intended only for testing purposes, so a PGT can be created
        without a valid callback URL present.
        """
        pgtid = self.create_ticket_str()
        pgtiou = self.create_ticket_str(prefix=self.model.IOU_PREFIX)
        try:
            if validate:
                self.validate_pgturl(pgturl, pgtid, pgtiou)
        except InternalError as e:
            # pgtUrl validation failed, so nothing has been created
            logger.warning("%s %s" % (e.code, e))
            return None
        else:
            # pgtUrl validation succeeded, so create a new PGT with the
            # already created ticket strings
            return super(ProxyGrantingTicketManager, self).create_ticket(ticket=pgtid,
                                                                         iou=pgtiou,
                                                                         **kwargs)

    def validate_pgturl(self, pgturl, pgtid, pgtiou):
        """
        Verify the provided proxy callback URL. This verification process
        requires three steps:

        1. The URL scheme must be HTTPS
        2. The SSL certificate must be valid and its name must match that
           of the service
        3. The callback URL must respond with a 200 or 3xx response code

        It is not required for validation that 3xx redirects be followed.
        """
        # Ensure the scheme is HTTPS before proceeding
        if not is_scheme_https(pgturl):
            raise InternalError("Proxy callback URL scheme is not HTTPS")

        # Connect to proxy callback URL, checking the SSL certificate
        pgturl = add_query_params(pgturl, {'pgtId': pgtid, 'pgtIou': pgtiou})
        try:
            verify = os.environ.get('REQUESTS_CA_BUNDLE', True)
            r = requests.get(pgturl, verify=verify)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.SSLError) as e:
            raise InternalError("%s" % e)

        # Check the returned HTTP status code
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise InternalError("Proxy callback returned %s" % e)

    def validate_ticket(self, ticket, service):
        """
        Given a ticket string, validate the corresponding ``Ticket``
        returning the ``Ticket`` if valid. If validation fails, raise
        an appropriate error.
        """
        if not ticket:
            raise InvalidRequestError("No ticket string provided")

        if not service:
            raise InvalidRequestError("No service identifier provided")

        if not self.model.TICKET_RE.match(ticket):
            raise InvalidTicketError("Ticket string %s is invalid" % ticket)

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            raise BadPGTError("Ticket %s does not exist" % ticket)

        if t.is_consumed():
            raise InvalidTicketError("%s %s has already been used" %
                                     (t.name, ticket))

        if not is_valid_service_url(service):
            raise InvalidServiceError("Service %s is not a valid %s URL" %
                                      (service, t.name))

        logger.debug("Validated %s %s" % (t.name, ticket))
        return t


class ProxyGrantingTicket(Ticket):
    """
    (3.3) A ``ProxyGrantingTicket`` is used by a service to obtain proxy
    tickets for obtaining access to a back-end service on behalf of a
    client. It is obtained upon validation of a ``ServiceTicket`` or a
    ``ProxyTicket``.
    """
    TICKET_PREFIX = 'PGT'
    IOU_PREFIX = 'PGTIOU'

    iou = models.CharField(_('iou'), max_length=255, unique=True)
    granted_by_st = models.ForeignKey(ServiceTicket, null=True, blank=True,
                                      verbose_name=_('granted by service ticket'))
    granted_by_pt = models.ForeignKey(ProxyTicket, null=True, blank=True,
                                      verbose_name=_('granted by proxy ticket'))

    objects = ProxyGrantingTicketManager()

    class Meta:
        verbose_name = _('proxy-granting ticket')
        verbose_name_plural = _('proxy-granting tickets')
