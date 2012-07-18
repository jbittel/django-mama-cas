import re
from datetime import timedelta
import logging

from django.test import TestCase
from django.utils.timezone import now
from django.core import management
from django.contrib.auth.models import User

from mama_cas.models import ServiceTicket
from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidTicketError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import InternalError


logging.disable(logging.CRITICAL)


class ServiceTicketTests(TestCase):
    """
    Test the model and manager used for ``ServiceTicket``s.
    """
    valid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_st_regexp = '^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = { 'username': 'ellen',
                  'password': 'mamas&papas',
                  'email': 'ellen@example.com' }
    ticket_info = { 'service': valid_service }

    def setUp(self):
        """
        Create a test user for authentication purposes and update the ticket
        information dictionary with the created user.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({'user': self.user})

    def test_create_ticket(self):
        """
        A new ``ServiceTicket`` ought to exist in the database with a valid
        ticket string, be neither consumed or expired and be related to the
        ``User`` that authorized its creation.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertTrue(re.search(self.valid_st_regexp, st.ticket))
        self.assertFalse(st.is_consumed())
        self.assertFalse(st.is_expired())
        self.assertEqual(st.user, self.user)

    def test_validate_ticket(self):
        """
        ``validate_ticket()`` ought to return the correct ``ServiceTicket``
        when provided with a valid ticket string and data. The validation
        process ought to consume the ``ServiceTicket``.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertTrue(ServiceTicket.objects.validate_ticket(st.ticket,
                                                              service=self.valid_service), st)
        # The ticket was consumed in the preceeding test
        self.assertRaises(InvalidTicketError, ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.valid_service)

    def test_validate_ticket_no_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when no ticket
        string is provided.
        """
        self.assertRaises(InvalidRequestError, ServiceTicket.objects.validate_ticket, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail when no service
        identifier is provided.
        """
        self.assertRaises(InvalidRequestError, ServiceTicket.objects.validate_ticket,
                          self.valid_st_str, service=None)

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when an invalid
        ticket string is provided.
        """
        self.assertRaises(InvalidTicketError, ServiceTicket.objects.validate_ticket,
                          '12345', service=self.valid_service)

    def test_validate_ticket_nonexistent_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when a ticket
        cannot be found in the database.
        """
        self.assertRaises(InvalidTicketError, ServiceTicket.objects.validate_ticket,
                          self.valid_st_str, service=self.valid_service)

    def test_validate_ticket_invalid_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail when a service
        identifier is provided that does not match the ticket's service
        identifier.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidServiceError, ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.invalid_service)

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when an expired
        ticket is provided.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        st.created = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        st.save()
        self.assertRaises(InvalidTicketError, ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.valid_service)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when a consumed
        ticket is provided.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        st.consume()
        self.assertRaises(InvalidTicketError, ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.valid_service)

    def test_validate_ticket_renew(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should only succeed if the ticket was issued from
        the presentation of the user's primary credentials.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidTicketError, ServiceTicket.objects.validate_ticket,
                          st.ticket,
                          service=self.valid_service,
                          renew=True)

        st = ServiceTicket.objects.create_ticket(primary=True, **self.ticket_info)
        self.assertTrue(ServiceTicket.objects.validate_ticket(st.ticket,
                                                              service=st.service,
                                                              renew=True), st)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``ServiceTicket.objects.delete_invalid_tickets()`` should
        only delete ``ServiceTicket``s that are either expired or consumed.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st.created = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        expired_st.save()
        consumed_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        consumed_st.consume()

        ServiceTicket.objects.delete_invalid_tickets()
        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get,
                          ticket=expired_st.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get,
                          ticket=consumed_st.ticket)

    def test_consume_tickets(self):
        """
        Calling ``ServiceTicket.objects.consume_tickets()`` should consume
        tickets belonging to the provided user.
        """
        st1 = ServiceTicket.objects.create_ticket(**self.ticket_info)
        st2 = ServiceTicket.objects.create_ticket(**self.ticket_info)

        ServiceTicket.objects.consume_tickets(self.user)
        self.assertEqual(ServiceTicket.objects.get(ticket=st1).is_consumed(), True)
        self.assertEqual(ServiceTicket.objects.get(ticket=st2).is_consumed(), True)

    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should only delete
        ``ServiceTicket``s that are either expired or consumed.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st.created = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        expired_st.save()
        consumed_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        consumed_st.consume()

        management.call_command('cleanupcas')
        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get,
                          ticket=expired_st.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get,
                          ticket=consumed_st.ticket)
