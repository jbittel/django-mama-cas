import re
from datetime import timedelta
import logging

from django.test import TestCase
from django.utils.timezone import now
from django.core import management

from mama_cas.models import LoginTicket
from mama_cas.models import ServiceTicket
from mama_cas.models import TicketGrantingTicket


logging.disable(logging.CRITICAL)


class LoginTicketTests(TestCase):
    valid_lt_str = 'LT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def test_create_ticket(self):
        """
        A new ``LoginTicket`` ought to exist in the database with a valid
        ticket string, and be neither consumed or expired.

        """
        lt = LoginTicket.objects.create_ticket()

        self.assertEqual(LoginTicket.objects.count(), 1)
        self.assertTrue(re.search('^LT-[0-9]{10,}-[a-zA-Z0-9]{32}$', lt.ticket))
        self.assertFalse(lt.is_consumed())
        self.assertFalse(lt.is_expired())

    def test_validate_ticket(self):
        """
        A ``LoginTicket`` ought to validate correctly when it has a valid
        ticket string that exists in the database, and when it is neither
        expired or consumed. The validation process ought to consume the
        ``LoginTicket``.

        """
        lt = LoginTicket.objects.create_ticket()

        self.assertFalse(LoginTicket.objects.validate_ticket(False))
        self.assertFalse(LoginTicket.objects.validate_ticket('12345'))
        self.assertFalse(LoginTicket.objects.validate_ticket(self.valid_lt_str))
        self.assertEqual(LoginTicket.objects.validate_ticket(lt.ticket), lt)

        lt.created_on = now() - timedelta(minutes=lt.TICKET_EXPIRE + 1)
        lt.consumed = None
        lt.save()
        self.assertFalse(LoginTicket.objects.validate_ticket(lt.ticket))
        self.assertFalse(LoginTicket.objects.validate_ticket(lt.ticket))

    def test_delete_invalid_tickets(self):
        """
        A ``LoginTicket`` ought be deleted when it is either expired or
        consumed, but not when it is valid.

        """
        valid_lt = LoginTicket.objects.create_ticket()
        consumed_lt = LoginTicket.objects.create_ticket()
        consumed_lt.consume()
        expired_lt = LoginTicket.objects.create_ticket()
        expired_lt.created_on = now() - timedelta(minutes=expired_lt.TICKET_EXPIRE + 1)
        expired_lt.save()

        self.assertEqual(LoginTicket.objects.count(), 3)
        LoginTicket.objects.delete_invalid_tickets()
        self.assertEqual(LoginTicket.objects.count(), 1)
        self.assertTrue(LoginTicket.objects.validate_ticket(valid_lt.ticket))
        self.assertFalse(LoginTicket.objects.validate_ticket(consumed_lt.ticket))
        self.assertFalse(LoginTicket.objects.validate_ticket(expired_lt.ticket))

    def test_management_command(self):
        """
        A ``LoginTicket`` ought be deleted using the ``cleanupcas`` managment
        command when it is either expired or consumed, but not when it is
        valid.

        """
        valid_lt = LoginTicket.objects.create_ticket()
        consumed_lt = LoginTicket.objects.create_ticket()
        consumed_lt.consume()
        expired_lt = LoginTicket.objects.create_ticket()
        expired_lt.created_on = now() - timedelta(minutes=expired_lt.TICKET_EXPIRE + 1)
        expired_lt.save()

        self.assertEqual(LoginTicket.objects.count(), 3)
        management.call_command('cleanupcas')
        self.assertEqual(LoginTicket.objects.count(), 1)

class ServiceTicketTests(TestCase):
    valid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ticket_info = {'service': 'http://www.test.com/'}

    def setUp(self):
        self.tgt = TicketGrantingTicket.objects.create_ticket(username='Test', client_ip='127.0.0.1')
        self.ticket_info.update({'granted_by_tgt': self.tgt})

    def test_create_ticket(self):
        """
        A new ``ServiceTicket`` ought to exist in the database with a valid
        ticket string and be neither consumed or expired. Additionally, it
        should be related to the ``TicketGrantingTicket`` that authorized
        its creation.

        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertTrue(re.search('^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$', st.ticket))
        self.assertFalse(st.is_consumed())
        self.assertFalse(st.is_expired())
        self.assertEqual(st.granted_by_tgt, self.tgt)

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

class TicketGrantingTicketTests(TestCase):
    valid_tgc_str = 'TGC-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ticket_info = {'username': 'Test',
                   'client_ip': '127.0.0.1'}

    def test_create_ticket(self):
        """
        A new ``TicketGrantingTicket`` ought to exist in the database with
        a valid ticket string and be neither consumed or expired.
        Additionally, it should contain the client IP that was passed to
        its creation function.

        """
        tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(TicketGrantingTicket.objects.count(), 1)
        self.assertTrue(re.search('^TGC-[0-9]{10,}-[a-zA-Z0-9]{32}$', tgt.ticket))
        self.assertEqual(tgt.client_ip, self.ticket_info['client_ip'])
        self.assertFalse(tgt.is_consumed())
        self.assertFalse(tgt.is_expired())

    def test_validate_ticket(self):
        """
        A ``TicketGrantingTicket`` ought to validate correctly when it has
        a valid ticket string that exists in the database, and when it is
        neither expired or consumed.

        """
        tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)

        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(False))
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket('12345'))
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(self.valid_tgc_str))
        self.assertEqual(TicketGrantingTicket.objects.validate_ticket(tgt.ticket, consume=False), tgt)
        # Run this test twice to ensure the ticket is not consumed
        self.assertEqual(TicketGrantingTicket.objects.validate_ticket(tgt.ticket), tgt)

        tgt.created_on = now() - timedelta(minutes=tgt.TICKET_EXPIRE + 1)
        tgt.save()
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(tgt.ticket))

        tgt.consume()
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(tgt.ticket))

    def test_consume_ticket(self):
        """
        A ``TicketGrantingTicket`` ought to be consumed properly when a
        valid ticket string is provided. Once consumed, the ticket should
        no longer successfully validate. 

        """
        tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        tgc = tgt.ticket

        self.assertFalse(TicketGrantingTicket.objects.consume_ticket('12345'))
        self.assertFalse(TicketGrantingTicket.objects.consume_ticket(False))
        self.assertFalse(TicketGrantingTicket.objects.consume_ticket(self.valid_tgc_str))
        self.assertEqual(TicketGrantingTicket.objects.consume_ticket(tgc), tgt)
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(tgc))

    def test_delete_invalid_tickets(self):
        """
        A ``TicketGrantingTicket`` ought to be deleted when it is either
        consumed or expired, but not when it is valid. Additionally, a
        delete should cascade to all associated ``ServiceTicket``s.

        """
        service = 'http://www.test.com/'

        valid_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.consume_ticket(consumed_tgt.ticket)
        expired_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        expired_tgt.created_on = now() - timedelta(minutes=expired_tgt.TICKET_EXPIRE + 1)
        expired_tgt.save()
        st = ServiceTicket.objects.create_ticket(service=service, granted_by_tgt=expired_tgt)

        self.assertEqual(TicketGrantingTicket.objects.count(), 3)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        TicketGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)
        self.assertEqual(ServiceTicket.objects.count(), 0)
        self.assertTrue(TicketGrantingTicket.objects.validate_ticket(valid_tgt.ticket))
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(consumed_tgt.ticket))
        self.assertFalse(TicketGrantingTicket.objects.validate_ticket(expired_tgt.ticket))

    def test_management_command(self):
        """
        A ``TicketGrantingTicket`` ought to be deleted using the ``cleanupcas``
        management command when it is either consumed or expired; otherwise
        it should be left alone. Additionally, a delete should cascade to all
        associated ``ServiceTicket``s.

        """
        service = 'http://www.test.com/'

        valid_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.consume_ticket(consumed_tgt.ticket)
        expired_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        expired_tgt.created_on = now() - timedelta(minutes=expired_tgt.TICKET_EXPIRE + 1)
        expired_tgt.save()
        st = ServiceTicket.objects.create_ticket(service=service, granted_by_tgt=expired_tgt)

        self.assertEqual(TicketGrantingTicket.objects.count(), 3)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        management.call_command('cleanupcas')
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)
        self.assertEqual(ServiceTicket.objects.count(), 0)
