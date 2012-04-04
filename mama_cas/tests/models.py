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
        lt = LoginTicket.objects.create_ticket()

        self.assertEqual(LoginTicket.objects.count(), 1)
        self.failUnless(re.search('^LT-[0-9]{10,}-[a-zA-Z0-9]{32}$', lt.ticket))
        self.failIf(lt.is_consumed())
        self.failIf(lt.is_expired())

    def test_validate_ticket(self):
        lt = LoginTicket.objects.create_ticket()

        self.failIf(LoginTicket.objects.validate_ticket(False))
        self.failIf(LoginTicket.objects.validate_ticket('12345'))
        self.failIf(LoginTicket.objects.validate_ticket(self.valid_lt_str))
        self.assertEqual(LoginTicket.objects.validate_ticket(lt.ticket), lt)

        lt.created_on = now() - timedelta(minutes=lt.TICKET_EXPIRE + 1)
        lt.save()
        self.failIf(LoginTicket.objects.validate_ticket(lt.ticket))

        lt.consume()
        self.failIf(LoginTicket.objects.validate_ticket(lt.ticket))

    def test_delete_invalid_tickets(self):
        valid_lt = LoginTicket.objects.create_ticket()
        consumed_lt = LoginTicket.objects.create_ticket()
        consumed_lt.consume()
        expired_lt = LoginTicket.objects.create_ticket()
        expired_lt.created_on = now() - timedelta(minutes=expired_lt.TICKET_EXPIRE + 1)
        expired_lt.save()

        self.assertEqual(LoginTicket.objects.count(), 3)
        LoginTicket.objects.delete_invalid_tickets()
        self.assertEqual(LoginTicket.objects.count(), 1)
        self.failUnless(LoginTicket.objects.validate_ticket(valid_lt.ticket))
        self.failIf(LoginTicket.objects.validate_ticket(consumed_lt.ticket))
        self.failIf(LoginTicket.objects.validate_ticket(expired_lt.ticket))

    def test_management_command(self):
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
        self.tgt = TicketGrantingTicket.objects.create_ticket(username='Test', host='localhost')
        self.ticket_info.update({'tgt': self.tgt})

    def test_create_ticket(self):
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.failUnless(re.search('^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$', st.ticket))
        self.failIf(st.is_consumed())
        self.failIf(st.is_expired())

    def test_validate_ticket(self):
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        service = 'http://www.test.com/'
        renew = 'true'

        self.failIf(ServiceTicket.objects.validate_ticket(False, False, renew))
        self.failIf(ServiceTicket.objects.validate_ticket('12345', service, renew))
        self.failIf(ServiceTicket.objects.validate_ticket(self.valid_st_str, service, renew))
        self.failIf(ServiceTicket.objects.validate_ticket(st.ticket, 'http://www.test.net/', renew))
        self.assertEqual(ServiceTicket.objects.validate_ticket(st.ticket, service, renew), st)

        st.created_on = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        st.save()
        self.failIf(ServiceTicket.objects.validate_ticket(st.ticket, service, renew))

        st.consume()
        self.failIf(ServiceTicket.objects.validate_ticket(st.ticket, service, renew))

class TicketGrantingTicketTests(TestCase):
    valid_tgc_str = 'TGC-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ticket_info = {'username': 'Test',
                   'host': 'localhost'}

    def test_create_ticket(self):
        tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(TicketGrantingTicket.objects.count(), 1)
        self.failUnless(re.search('^TGC-[0-9]{10,}-[a-zA-Z0-9]{32}$', tgt.ticket))
        self.failIf(tgt.is_consumed())
        self.failIf(tgt.is_expired())

    def test_validate_ticket(self):
        tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)

        self.failIf(TicketGrantingTicket.objects.validate_ticket(False))
        self.failIf(TicketGrantingTicket.objects.validate_ticket('12345'))
        self.failIf(TicketGrantingTicket.objects.validate_ticket(self.valid_tgc_str))
        self.assertEqual(TicketGrantingTicket.objects.validate_ticket(tgt.ticket), tgt)

        tgt.created_on = now() - timedelta(minutes=tgt.TICKET_EXPIRE + 1)
        tgt.save()
        self.failIf(TicketGrantingTicket.objects.validate_ticket(tgt.ticket))

        tgt.consume()
        self.failIf(TicketGrantingTicket.objects.validate_ticket(tgt.ticket))

    def test_consume_ticket(self):
        tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        tgc = tgt.ticket

        self.failIf(TicketGrantingTicket.objects.consume_ticket('12345'))
        self.failIf(TicketGrantingTicket.objects.consume_ticket(False))
        self.failIf(TicketGrantingTicket.objects.consume_ticket(self.valid_tgc_str))
        self.assertEqual(TicketGrantingTicket.objects.consume_ticket(tgc), tgt)
        self.failIf(TicketGrantingTicket.objects.validate_ticket(tgc))

    def test_delete_invalid_tickets(self):
        service = 'http://www.test.com/'

        valid_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.consume_ticket(consumed_tgt.ticket)
        expired_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        expired_tgt.created_on = now() - timedelta(minutes=expired_tgt.TICKET_EXPIRE + 1)
        expired_tgt.save()
        st = ServiceTicket.objects.create_ticket(service, expired_tgt)

        self.assertEqual(TicketGrantingTicket.objects.count(), 3)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        TicketGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)
        self.assertEqual(ServiceTicket.objects.count(), 0)
        self.failUnless(TicketGrantingTicket.objects.validate_ticket(valid_tgt.ticket))
        self.failIf(TicketGrantingTicket.objects.validate_ticket(consumed_tgt.ticket))
        self.failIf(TicketGrantingTicket.objects.validate_ticket(expired_tgt.ticket))

    def test_management_command(self):
        service = 'http://www.test.com/'

        valid_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        consumed_tgt = TicketGrantingTicket.objects.consume_ticket(consumed_tgt.ticket)
        expired_tgt = TicketGrantingTicket.objects.create_ticket(**self.ticket_info)
        expired_tgt.created_on = now() - timedelta(minutes=expired_tgt.TICKET_EXPIRE + 1)
        expired_tgt.save()
        st = ServiceTicket.objects.create_ticket(service, expired_tgt)

        self.assertEqual(TicketGrantingTicket.objects.count(), 3)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        management.call_command('cleanupcas')
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)
        self.assertEqual(ServiceTicket.objects.count(), 0)
