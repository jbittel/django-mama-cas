from __future__ import unicode_literals

from datetime import timedelta
import logging
import os
import re
import requests
import time

from django.conf import settings
from django.db import models
from django.db.models import Q
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

from mama_cas.exceptions import InvalidRequest
from mama_cas.exceptions import InvalidTicket
from mama_cas.exceptions import InvalidService
from mama_cas.exceptions import InternalError
from mama_cas.exceptions import BadPgt
from mama_cas.utils import add_query_params
from mama_cas.utils import is_scheme_https
from mama_cas.utils import clean_service_url
from mama_cas.utils import is_valid_service_url


logger = logging.getLogger(__name__)


class TicketManager(models.Manager):
    def create_ticket(self, ticket=None, **kwargs):
        """
        Create a new ``Ticket``. Additional arguments are passed to the
        ``create()`` function. Return the newly created ``Ticket``.
        """
        if not ticket:
            ticket = self.create_ticket_str()
        if 'service' in kwargs:
            kwargs['service'] = clean_service_url(kwargs['service'])
        expires = timezone.now() + timedelta(seconds=self.model.TICKET_EXPIRE)
        t = self.create(ticket=ticket, expires=expires, **kwargs)
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

    def validate_ticket(self, ticket, service, renew=False):
        """
        Given a ticket string and service identifier, validate the
        corresponding ``Ticket``. If validation succeeds, return the
        ``Ticket``. If validation fails, raise an appropriate error.

        If ``renew`` is provided, the validation will only succeed if the
        ticket was issued from the presentation of the user's primary
        credentials.
        """
        if not ticket:
            raise InvalidRequest("No ticket string provided")

        if not self.model.TICKET_RE.match(ticket):
            raise InvalidTicket("Ticket string %s is invalid" % ticket)

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            raise InvalidTicket("Ticket %s does not exist" % ticket)

        if t.is_consumed():
            raise InvalidTicket("%s %s has already been used" %
                                (t.name, ticket))
        t.consume()

        if t.is_expired():
            raise InvalidTicket("%s %s has expired" % (t.name, ticket))

        if not service:
            raise InvalidRequest("No service identifier provided")

        if not is_valid_service_url(service):
            raise InvalidService("Service %s is not a valid %s URL" %
                                 (service, t.name))

        if not same_origin(t.service, service):
            raise InvalidService("%s %s for service %s is invalid for service "
                                 "%s" % (t.name, ticket, t.service, service))

        if renew and not t.is_primary():
            raise InvalidTicket("%s %s was not issued via primary "
                                "credentials" % (t.name, ticket))

        logger.debug("Validated %s %s" % (t.name, ticket))
        return t

    def delete_invalid_tickets(self):
        """
        Delete consumed or expired ``Ticket``s that are not referenced
        by other ``Ticket``s. Invalid tickets are no longer valid for
        authentication and can be safely deleted.

        A custom management command is provided that executes this method
        on all applicable models by running ``manage.py cleanupcas``.
        This command should be run on a regular basis to prevent invalid
        tickets from causing storage or performance issues.
        """
        for ticket in self.filter(Q(consumed__isnull=False) |
                                  Q(expires__lte=timezone.now())):
            try:
                ticket.delete()
            except models.ProtectedError:
                pass

    def consume_tickets(self, user):
        """
        Consume all valid ``Ticket``s for a specified user. This is run
        when the user logs out to ensure all issued tickets are no longer
        valid for future authentication attempts.
        """
        for ticket in self.filter(user=user, consumed__isnull=True,
                                  expires__gt=timezone.now()):
            ticket.consume()


@python_2_unicode_compatible
class Ticket(models.Model):
    """
    ``Ticket`` is an abstract base class implementing common methods
    and fields for CAS tickets.
    """
    TICKET_EXPIRE = getattr(settings, 'MAMA_CAS_TICKET_EXPIRE', 90)
    TICKET_RAND_LEN = getattr(settings, 'MAMA_CAS_TICKET_RAND_LEN', 32)
    TICKET_RE = re.compile("^[A-Z]{2,3}-[0-9]{10,}-[a-zA-Z0-9]{%d}$" % TICKET_RAND_LEN)

    ticket = models.CharField(_('ticket'), max_length=255, unique=True)
    user = models.ForeignKey(User, verbose_name=_('user'))
    expires = models.DateTimeField(_('expires'))
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
        Consume a ``Ticket`` by populating the ``consumed`` field with
        the current datetime. A consumed ``Ticket`` is invalid for future
        authentication attempts.
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
        return self.expires <= timezone.now()


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
                                       on_delete=models.PROTECT,
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
            raise InternalError("Proxy callback %s is not HTTPS" % pgturl)

        # Connect to proxy callback URL, checking the SSL certificate
        pgturl = add_query_params(pgturl, {'pgtId': pgtid, 'pgtIou': pgtiou})
        try:
            verify = os.environ.get('REQUESTS_CA_BUNDLE', True)
            r = requests.get(pgturl, verify=verify)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.SSLError) as e:
            raise InternalError("Proxy callback %s returned %s" % (pgturl, e))

        # Check the returned HTTP status code
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise InternalError("Proxy callback %s returned %s" % (pgturl, e))

    def validate_ticket(self, ticket, service):
        """
        Given a ticket string and service identifier, validate the
        corresponding ``Ticket``. If validation succeeds, return the
        ``Ticket``. If validation fails, raise an appropriate error.
        """
        if not ticket:
            raise InvalidRequest("No ticket string provided")

        if not service:
            raise InvalidRequest("No service identifier provided")

        if not self.model.TICKET_RE.match(ticket):
            raise InvalidTicket("Ticket string %s is invalid" % ticket)

        try:
            t = self.get(ticket=ticket)
        except self.model.DoesNotExist:
            raise BadPgt("Ticket %s does not exist" % ticket)

        if t.is_consumed():
            raise InvalidTicket("%s %s has already been used" %
                                (t.name, ticket))

        if t.is_expired():
            raise InvalidTicket("%s %s has expired" % (t.name, ticket))

        if not is_valid_service_url(service):
            raise InvalidService("Service %s is not a valid %s URL" %
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
    TICKET_EXPIRE = getattr(settings, 'SESSION_COOKIE_AGE')

    iou = models.CharField(_('iou'), max_length=255, unique=True)
    granted_by_st = models.ForeignKey(ServiceTicket, null=True, blank=True,
                                      on_delete=models.PROTECT,
                                      verbose_name=_('granted by service ticket'))
    granted_by_pt = models.ForeignKey(ProxyTicket, null=True, blank=True,
                                      on_delete=models.PROTECT,
                                      verbose_name=_('granted by proxy ticket'))

    objects = ProxyGrantingTicketManager()

    class Meta:
        verbose_name = _('proxy-granting ticket')
        verbose_name_plural = _('proxy-granting tickets')
