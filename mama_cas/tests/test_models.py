from datetime import timedelta
from mock import patch
import re

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import now

import requests

from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from .factories import UserFactory
from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ServiceTicket
from mama_cas.exceptions import InvalidProxyCallback
from mama_cas.exceptions import InvalidRequest
from mama_cas.exceptions import InvalidService
from mama_cas.exceptions import InvalidTicket
from mama_cas.exceptions import UnauthorizedServiceProxy


class TicketManagerTests(TestCase):
    """
    Test the ``TicketManager`` model manager.
    """
    url = 'http://www.example.com/'

    def setUp(self):
        self.user = UserFactory()

    def test_create_ticket(self):
        """
        A ticket ought to be created with a generated ticket string.
        """
        st = ServiceTicket.objects.create_ticket(user=self.user)
        self.assertTrue(re.search(st.TICKET_RE, st.ticket))

    def test_create_ticket_ticket(self):
        """
        A ticket ought to be created with a provided ticket string,
        if present.
        """
        ticket = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        st = ServiceTicket.objects.create_ticket(ticket=ticket, user=self.user)
        self.assertEqual(st.ticket, ticket)

    def test_create_ticket_service(self):
        """
        If a service is provided, it should be cleaned.
        """
        service = 'http://www.example.com/test?test3=blue#green'
        st = ServiceTicket.objects.create_ticket(service=service, user=self.user)
        self.assertEqual(st.service, 'http://www.example.com/test')

    def test_create_ticket_no_expires(self):
        """
        A ticket ought to be created with a calculated expiry value.
        """
        st = ServiceTicket.objects.create_ticket(user=self.user)
        self.assertTrue(st.expires > now())

    def test_create_ticket_expires(self):
        """
        A ticket ought to be created with a provided expiry value,
        if present.
        """
        expires = now() + timedelta(seconds=30)
        st = ServiceTicket.objects.create_ticket(expires=expires, user=self.user)
        self.assertEqual(st.expires, expires)

    def test_create_ticket_str(self):
        """
        A ticket string should be created with the appropriate model
        prefix and format.
        """
        str = ServiceTicket.objects.create_ticket_str()
        self.assertTrue(re.search('^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$', str))

    def test_create_ticket_str_prefix(self):
        """
        A ticket string should be created with the provided prefix
        string and format.
        """
        str = ProxyGrantingTicket.objects.create_ticket_str(prefix='PGTIOU')
        self.assertTrue(re.search('^PGTIOU-[0-9]{10,}-[a-zA-Z0-9]{32}$', str))

    def test_validate_ticket(self):
        """
        Validation ought to succeed when provided with a valid ticket
        string and data. The ticket ought to be consumed in the process.
        """
        st = ServiceTicketFactory()
        ticket = ServiceTicket.objects.validate_ticket(st.ticket, self.url)
        self.assertEqual(ticket, st)
        self.assertTrue(ticket.is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The validation process ought to fail when no ticket string is
        provided.
        """
        with self.assertRaises(InvalidRequest):
            ServiceTicket.objects.validate_ticket(None, self.url)

    def test_validate_ticket_invalid_ticket(self):
        """
        The validation process ought to fail when an invalid ticket
        string is provided.
        """
        with self.assertRaises(InvalidTicket):
            ServiceTicket.objects.validate_ticket('12345', self.url)

    def test_validate_ticket_does_not_exist(self):
        """
        The validation process ought to fail when a valid ticket string
        cannot be found in the database.
        """
        ticket = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        with self.assertRaises(InvalidTicket):
            ServiceTicket.objects.validate_ticket(ticket, self.url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The validation process ought to fail when a consumed ticket
        is provided.
        """
        st = ServiceTicketFactory(consume=True)
        with self.assertRaises(InvalidTicket):
            ServiceTicket.objects.validate_ticket(st.ticket, self.url)

    def test_validate_ticket_expired_ticket(self):
        """
        The validation process ought to fail when an expired ticket
        is provided.
        """
        st = ServiceTicketFactory(expire=True)
        with self.assertRaises(InvalidTicket):
            ServiceTicket.objects.validate_ticket(st.ticket, self.url)

    def test_validate_ticket_no_service(self):
        """
        The validation process ought to fail when no service identifier
        is provided. The ticket ought to be consumed in the process.
        """
        st = ServiceTicketFactory()
        with self.assertRaises(InvalidRequest):
            ServiceTicket.objects.validate_ticket(st.ticket, None)
        st = ServiceTicket.objects.get(ticket=st.ticket)
        self.assertTrue(st.is_consumed())

    def test_validate_ticket_invalid_service(self):
        """
        The validation process ought to fail when an invalid service
        identifier is provided.
        """
        service = 'http://www.example.org'
        st = ServiceTicketFactory()
        with self.assertRaises(InvalidService):
            ServiceTicket.objects.validate_ticket(st.ticket, service)

    def test_validate_ticket_service_mismatch(self):
        """
        The validation process ought to fail when the provided service
        identifier does not match the ticket's service.
        """
        service = 'http://sub.example.com/'
        st = ServiceTicketFactory()
        with self.assertRaises(InvalidService):
            ServiceTicket.objects.validate_ticket(st.ticket, service)

    def test_validate_ticket_renew(self):
        """
        When ``renew`` is set, the validation process should succeed
        if the ticket was issued from the presentation of the user's
        primary credentials.
        """
        st = ServiceTicketFactory(primary=True)
        ticket = ServiceTicket.objects.validate_ticket(st.ticket, self.url,
                                                       renew=True)
        self.assertEqual(ticket, st)

    def test_validate_ticket_renew_secondary(self):
        """
        When ``renew`` is set, the validation process should fail if
        the ticket was not issued from the presentation of the user's
        primary credentials.
        """
        st = ServiceTicketFactory()
        with self.assertRaises(InvalidTicket):
            ServiceTicket.objects.validate_ticket(st.ticket, self.url,
                                                  renew=True)

    def test_delete_invalid_tickets(self):
        """
        Expired or consumed tickets should be deleted. Invalid tickets
        referenced by other tickets should not be deleted.
        """
        ServiceTicketFactory()  # Should not be deleted
        expired = ServiceTicketFactory(expire=True)
        consumed = ServiceTicketFactory(consume=True)
        referenced = ServiceTicketFactory(consume=True)  # Should not be deleted
        ProxyGrantingTicketFactory(granted_by_st=referenced)
        ServiceTicket.objects.delete_invalid_tickets()

        self.assertEqual(ServiceTicket.objects.count(), 2)
        self.assertRaises(ServiceTicket.DoesNotExist,
                          ServiceTicket.objects.get,
                          ticket=expired.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist,
                          ServiceTicket.objects.get,
                          ticket=consumed.ticket)

    def test_consume_tickets(self):
        """
        All tickets belonging to the specified user should be consumed.
        """
        st1 = ServiceTicketFactory()
        st2 = ServiceTicketFactory()
        ServiceTicket.objects.consume_tickets(self.user)
        self.assertTrue(ServiceTicket.objects.get(ticket=st1).is_consumed())
        self.assertTrue(ServiceTicket.objects.get(ticket=st2).is_consumed())


class TicketTests(TestCase):
    """
    Test the ``Ticket`` abstract model.
    """
    def test_ticket_consumed(self):
        """
        ``is_consumed()`` should return ``True`` for a consumed ticket.
        """
        st = ServiceTicketFactory()
        st.consume()
        st = ServiceTicket.objects.get(ticket=st.ticket)
        self.assertTrue(st.is_consumed())

    def test_ticket_not_consumed(self):
        """
        ``is_consumed()`` should return ``False`` for a valid ticket.
        """
        st = ServiceTicketFactory()
        self.assertFalse(st.is_consumed())

    def test_ticket_expired(self):
        """
        ``is_expired()`` should return ``True`` for an expired ticket.
        """
        st = ServiceTicketFactory(expire=True)
        self.assertTrue(st.is_expired())

    def test_ticket_not_expired(self):
        """
        ``is_expired()`` should return ``False`` for a valid ticket.
        """
        st = ServiceTicketFactory()
        self.assertFalse(st.is_expired())


@override_settings(MAMA_CAS_ENABLE_SINGLE_SIGN_OUT=True)
class ServiceTicketManagerTests(TestCase):
    """
    Test the ``ServiceTicketManager`` model manager.
    """
    def setUp(self):
        self.user = UserFactory()

    def test_request_sign_out(self):
        """
        Calling the ``request_sign_out()`` manager method should
        issue a POST request for each consumed ticket for the
        provided user.
        """
        ServiceTicketFactory(consume=True)
        ServiceTicketFactory(consume=True)
        with patch('requests.post') as mock:
            mock.return_value.status_code = 200
            ServiceTicket.objects.request_sign_out(self.user)
            self.assertEqual(mock.call_count, 2)

    @override_settings(MAMA_CAS_ASYNC_CONCURRENCY=0)
    def test_request_sign_out_no_pool(self):
        """
        Calling the ``request_sign_out()`` manager method with
        concurrency disabled should issue a POST request for each
        consumed ticket for the provided user.
        """
        ServiceTicketFactory(consume=True)
        ServiceTicketFactory(consume=True)
        with patch('requests.post') as mock:
            mock.return_value.status_code = 200
            ServiceTicket.objects.request_sign_out(self.user)
            self.assertEqual(mock.call_count, 2)


class ServiceTicketTests(TestCase):
    """
    Test the ``ServiceTicket`` model.
    """
    def test_create_service_ticket(self):
        """
        A ``ServiceTicket`` ought to be created with an appropriate
        prefix.
        """
        st = ServiceTicketFactory()
        self.assertTrue(st.ticket.startswith(st.TICKET_PREFIX))

    def test_primary(self):
        """
        ``is_primary()`` should return ``True`` if the ``ServiceTicket``
        was created from the presentation of a user's credentials.
        """
        st = ServiceTicketFactory(primary=True)
        self.assertTrue(st.is_primary())

    def test_secondary(self):
        """
        ``is_primary()`` should return ``False`` if the ``ServiceTicket``
        was not created from the presentation of a user's credentials.
        """
        st = ServiceTicketFactory()
        self.assertFalse(st.is_primary())

    def test_request_sign_out(self):
        """
        A successful sign-out request to a service should not
        cause any side-effects.
        """
        st = ServiceTicketFactory()
        with patch('requests.post') as mock:
            mock.return_value.status_code = 200
            st.request_sign_out()

    def test_request_sign_out_exception(self):
        """
        If a sign-out request to a service raises an exception,
        it should be handled.
        """
        st = ServiceTicketFactory()
        with patch('requests.post') as mock:
            mock.side_effect = requests.exceptions.RequestException
            st.request_sign_out()

    def test_request_sign_out_invalid_status(self):
        """
        If a sign-out request to a service returns an invalid
        status code, the resulting exception should be handled.
        """
        st = ServiceTicketFactory()
        with patch('requests.post') as mock:
            mock.return_value.status_code = 500
            st.request_sign_out()

    def test_request_sign_out_logout_allow_false(self):
        """
        If SLO requests are disabled for a service, the logout
        request should not be sent.
        """
        st = ServiceTicketFactory(service='http://example.com')
        with patch('requests.post') as mock:
            mock.return_value.status_code = 500
            st.request_sign_out()
            self.assertEqual(mock.call_count, 0)


class ProxyTicketTests(TestCase):
    """
    Test the ``ProxyTicket`` model.
    """
    def test_create_proxy_ticket(self):
        """
        A ``ProxyTicket`` ought to be created with an appropriate
        prefix.
        """
        pt = ProxyTicketFactory()
        self.assertTrue(pt.ticket.startswith(pt.TICKET_PREFIX))


class ProxyGrantingTicketManager(TestCase):
    """
    Test the ``ProxyGrantingTicketManager`` model manager.
    """
    def setUp(self):
        self.user = UserFactory()
        self.pt = ProxyTicketFactory()
        self.pgtid = ProxyGrantingTicket.objects.create_ticket_str()
        self.pgtiou = ProxyGrantingTicket.objects.create_ticket_str(prefix=ProxyGrantingTicket.IOU_PREFIX)

    def test_create_ticket(self):
        """
        A ``ProxyGrantingTicket`` ought to be created with the
        appropriate ticket strings.
        """
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            pgt = ProxyGrantingTicket.objects.create_ticket('https://www.example.com', 'https://www.example.com/',
                                                            user=self.user, granted_by_pt=self.pt)
        self.assertTrue(re.search(pgt.TICKET_RE, pgt.ticket))
        self.assertTrue(pgt.iou.startswith(pgt.IOU_PREFIX))

    def test_create_ticket_invalid_pgturl(self):
        """
        If callback validation fails, ``None`` should be returned
        instead of a ``ProxyGrantingTicket``.
        """
        with patch('requests.get') as mock:
            mock.side_effect = requests.exceptions.ConnectionError
            pgt = ProxyGrantingTicket.objects.create_ticket('https://www.example.com', 'https://www.example.com/',
                                                            user=self.user, granted_by_pt=self.pt)
            self.assertEqual(mock.call_count, 1)
        self.assertIsNone(pgt)

    def test_validate_callback(self):
        """
        If a valid PGTURL is provided, an exception should not be raised.
        """
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            try:
                ProxyGrantingTicket.objects.validate_callback('https://www.example.com', 'https://www.example.com/',
                                                              self.pgtid, self.pgtiou)
            except InvalidProxyCallback:
                self.fail("Exception raised validating proxy callback URL")
            self.assertEqual(mock.call_count, 2)

    def test_validate_callback_unauthorized_service(self):
        """
        If an unauthorized service is provided, `UnauthorizedServiceProxy`
        should be raised.
        """
        with self.assertRaises(UnauthorizedServiceProxy):
            ProxyGrantingTicket.objects.validate_callback('http://example.com/', 'https://www.example.com/',
                                                          self.pgtid, self.pgtiou)

    def test_validate_callback_http_pgturl(self):
        """
        If an HTTP PGTURL is provided, InvalidProxyCallback should be raised.
        """
        with self.assertRaises(InvalidProxyCallback):
            ProxyGrantingTicket.objects.validate_callback('http://www.example.com/', 'http://www.example.com/',
                                                          self.pgtid, self.pgtiou)

    def test_validate_callback_invalid_pgturl(self):
        """If an invalid PGTURL is provided, InvalidProxyCallback should be raised."""
        with self.assertRaises(InvalidProxyCallback):
            ProxyGrantingTicket.objects.validate_callback('http://www.example.com/', 'https://www.example.org/',
                                                          self.pgtid, self.pgtiou)

    def test_validate_callback_ssl_error(self):
        """
        If the validation request encounters an SSL error, an
        InvalidProxyCallback should be raised.
        """
        with patch('requests.get') as mock:
            mock.side_effect = requests.exceptions.SSLError
            with self.assertRaises(InvalidProxyCallback):
                ProxyGrantingTicket.objects.validate_callback('http://www.example.com/', 'https://www.example.org/',
                                                              self.pgtid, self.pgtiou)

    def test_validate_callback_connection_error(self):
        """
        If the validation request encounters an exception, an
        InvalidProxyCallback should be raised.
        """
        with patch('requests.get') as mock:
            mock.side_effect = requests.exceptions.ConnectionError
            with self.assertRaises(InvalidProxyCallback):
                ProxyGrantingTicket.objects.validate_callback('http://www.example.com/', 'https://www.example.org/',
                                                              self.pgtid, self.pgtiou)

    def test_validate_callback_invalid_status(self):
        """
        If the validation request returns an invalid status code, an
        InvalidProxyCallback should be raised.
        """
        with patch('requests.get') as mock:
            mock.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
            with self.assertRaises(InvalidProxyCallback):
                ProxyGrantingTicket.objects.validate_callback('http://www.example.com/', 'https://www.example.org/',
                                                              self.pgtid, self.pgtiou)

    def test_validate_ticket(self):
        """
        Validation ought to succeed when provided with a valid ticket
        string and data. The ticket should not be consumed in the
        process.
        """
        pgt = ProxyGrantingTicketFactory()
        ticket = ProxyGrantingTicket.objects.validate_ticket(pgt.ticket, 'https://www.example.com')
        self.assertEqual(ticket, pgt)
        self.assertFalse(ticket.is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The validation process ought to fail when no ticket string is
        provided.
        """
        with self.assertRaises(InvalidRequest):
            ProxyGrantingTicket.objects.validate_ticket(None, 'https://www.example.com')

    def test_validate_ticket_no_service(self):
        """
        The validation process ought to fail when no service identifier
        is provided.
        """
        pgt = ProxyGrantingTicketFactory()
        with self.assertRaises(InvalidRequest):
            ProxyGrantingTicket.objects.validate_ticket(pgt.ticket, None)

    def test_validate_ticket_invalid_ticket(self):
        """
        The validation process ought to fail when an invalid ticket
        string is provided.
        """
        with self.assertRaises(InvalidTicket):
            ProxyGrantingTicket.objects.validate_ticket('12345', 'https://www.example.com')

    def test_validate_ticket_does_not_exist(self):
        """
        The validation process ought to fail when a valid ticket string
        cannot be found in the database.
        """
        ticket = 'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        with self.assertRaises(InvalidTicket):
            ProxyGrantingTicket.objects.validate_ticket(ticket, 'https://www.example.com')

    def test_validate_ticket_consumed_ticket(self):
        """
        The validation process ought to fail when a consumed ticket
        is provided.
        """
        pgt = ProxyGrantingTicketFactory(consume=True)
        with self.assertRaises(InvalidTicket):
            ProxyGrantingTicket.objects.validate_ticket(pgt.ticket, 'https://www.example.com')

    def test_validate_ticket_expired_ticket(self):
        """
        The validation process ought to fail when an expired ticket
        is provided.
        """
        pgt = ProxyGrantingTicketFactory(expire=True)
        with self.assertRaises(InvalidTicket):
            ProxyGrantingTicket.objects.validate_ticket(pgt.ticket, 'https://www.example.com')

    def test_validate_ticket_invalid_service(self):
        """
        The validation process ought to fail when an invalid service
        identifier is provided.
        """
        pgt = ProxyGrantingTicketFactory()
        with self.assertRaises(InvalidService):
            ProxyGrantingTicket.objects.validate_ticket(pgt.ticket, 'http://www.example.org')


class ProxyGrantingTicketTests(TestCase):
    """
    Test the ``ProxyGrantingTicket`` model.
    """
    def test_create_proxy_granting_ticket(self):
        """
        A ``ProxyGrantingTicket`` ought to be created with an
        appropriate prefix.
        """
        pgt = ProxyGrantingTicketFactory()
        self.assertTrue(pgt.ticket.startswith(pgt.TICKET_PREFIX))
