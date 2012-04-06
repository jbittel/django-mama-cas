import re
from datetime import timedelta
import logging

from django.test import TestCase
from django.utils.timezone import now
from django.core import management
from django.contrib.auth.models import User

from mama_cas.models import ServiceTicket


logging.disable(logging.CRITICAL)


class ServiceTicketTests(TestCase):
    valid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ticket_info = {'service': 'http://www.test.com/'}

    def setUp(self):
        """
        Create a test user for authentication purposes.

        """
        self.user = User.objects.create_user('test', 'test@localhost.com', 'testing')
        self.ticket_info.update({'user': self.user})

    def test_create_ticket(self):
        """
        A new ``ServiceTicket`` ought to exist in the database with a valid
        ticket string and be neither consumed or expired. Additionally, it
        should be related to the ``User`` that authorized its creation.

        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertTrue(re.search('^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$', st.ticket))
        self.assertFalse(st.is_consumed())
        self.assertFalse(st.is_expired())
        self.assertEqual(st.user, self.user)

    def test_validate_ticket(self):
        """
        A ``ServiceTicket`` ought to validate correctly when it meets these
        criteria:

        1. Has a valid ticket string that exists in the database
        2. Is not expired or consumed
        3. Has a service that matches the provided service parameter

        If any of these conditions are not met the validation should fail.
        The validation process ought to consume the ``ServiceTicket``.

        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        service = 'http://www.test.com/'
        renew = 'true'

        self.assertFalse(ServiceTicket.objects.validate_ticket(False))
        self.assertFalse(ServiceTicket.objects.validate_ticket('12345', service=service))
        self.assertFalse(ServiceTicket.objects.validate_ticket(self.valid_st_str, service=service))
        self.assertFalse(ServiceTicket.objects.validate_ticket(st.ticket, service='http://www.test.net/'))
        # This test should fail, as the ticket was consumed in the preceeding test
        self.assertFalse(ServiceTicket.objects.validate_ticket(st.ticket, service=service), st)
        st.consumed = None
        st.save()
        self.assertTrue(ServiceTicket.objects.validate_ticket(st.ticket, service=service), st)

        st.created_on = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        st.save()
        self.assertFalse(ServiceTicket.objects.validate_ticket(st.ticket, service))

        st.consume()
        self.assertFalse(ServiceTicket.objects.validate_ticket(st.ticket, service))

    def test_invalid_ticket_deletion(self):
        """
        Calling ``ServiceTicket.objects.delete_invalid_tickets() should
        only delete ``ServiceTicket``s that are either expired or consumed.

        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st.created_on = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        expired_st.save()
        consumed_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        consumed_st.consume()

        ServiceTicket.objects.delete_invalid_tickets()
        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get, ticket=expired_st.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get, ticket=consumed_st.ticket)

    def test_management_command(self):
        """
        The ``cleanupcas`` management command should only delete
        ``ServiceTicket``s that are either expired or consumed.

        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st.created_on = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        expired_st.save()
        consumed_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        consumed_st.consume()

        management.call_command('cleanupcas')
        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get, ticket=expired_st.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist, ServiceTicket.objects.get, ticket=consumed_st.ticket)
