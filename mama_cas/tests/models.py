import re
from datetime import timedelta
import logging

from django.test import TestCase
from django.utils.timezone import now
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings

from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidTicketError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import BadPGTError


logging.disable(logging.CRITICAL)


class ServiceTicketTests(TestCase):
    """
    Test the model and manager used for ``ServiceTicket``s.
    """
    valid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_st_regexp = '^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    ticket_info = {'service': valid_service}

    def setUp(self):
        """
        Create a test user for authentication purposes and update the ticket
        information dictionary with the created user.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({'user': self.user})

        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

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
        self.assertTrue(ServiceTicket.objects.get(ticket=st.ticket).is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when no ticket
        string is provided.
        """
        self.assertRaises(InvalidRequestError, ServiceTicket.objects.validate_ticket, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail when no service
        identifier is provided and the ticket ought to be consumed.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidRequestError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service=None)
        self.assertTrue(ServiceTicket.objects.get(ticket=st.ticket).is_consumed())

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
        self.assertRaises(InvalidTicketError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket,
                          service=self.valid_service,
                          renew=True)

        st = ServiceTicket.objects.create_ticket(primary=True,
                                                 **self.ticket_info)
        self.assertEqual(ServiceTicket.objects.validate_ticket(st.ticket,
                                                               service=self.valid_service,
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


class ProxyTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyTicket``s.
    """
    valid_pt_str = 'PT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_pt_regexp = '^PT-[0-9]{10,}-[a-zA-Z0-9]{32}$'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    ticket_info = {'service': valid_service}

    def setUp(self):
        """
        Create a test user for authentication purposes and update the ticket
        information dictionary with the created user. Additionally, create a
        ``ProxyGrantingTicket`` to use as the "source" of the ``ProxyTicket``.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                             validate=False,
                                                             user=self.user)
        self.ticket_info.update({'user': self.user, 'granted_by_pgt': self.pgt})

        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_create_ticket(self):
        """
        A new ``ProxyTicket`` ought to exist in the database with a valid
        ticket string, be neither consumed or expired and be related to the
        ``User`` that authorized its creation.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)

        self.assertEqual(ProxyTicket.objects.count(), 1)
        self.assertTrue(re.search(self.valid_pt_regexp, pt.ticket))
        self.assertFalse(pt.is_consumed())
        self.assertFalse(pt.is_expired())
        self.assertEqual(pt.user, self.user)
        self.assertEqual(pt.granted_by_pgt, self.pgt)

    def test_validate_ticket(self):
        """
        ``validate_ticket()`` ought to return the correct ``ProxyTicket``
        when provided with a valid ticket string and data. The validation
        process ought to consume the ``ProxyTicket``.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertTrue(ProxyTicket.objects.validate_ticket(pt.ticket,
                                                            service=self.valid_service), pt)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt.ticket).is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when no ticket
        string is provided.
        """
        self.assertRaises(InvalidRequestError, ProxyTicket.objects.validate_ticket, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ProxyTicket`` validation process ought to fail when no service
        identifier is provided and the ticket ought to be consumed.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidRequestError,
                          ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=None)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt.ticket).is_consumed())

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when an invalid
        ticket string is provided.
        """
        self.assertRaises(InvalidTicketError, ProxyTicket.objects.validate_ticket,
                          '12345', service=self.valid_service)

    def test_validate_ticket_nonexistent_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when a ticket
        cannot be found in the database.
        """
        self.assertRaises(InvalidTicketError, ProxyTicket.objects.validate_ticket,
                          self.valid_pt_str, service=self.valid_service)

    def test_validate_ticket_invalid_service(self):
        """
        The ``ProxyTicket`` validation process ought to fail when a service
        identifier is provided that does not match the ticket's service
        identifier.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidServiceError, ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=self.invalid_service)

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when an expired
        ticket is provided.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        pt.created = now() - timedelta(minutes=pt.TICKET_EXPIRE + 1)
        pt.save()
        self.assertRaises(InvalidTicketError, ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=self.valid_service)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when a consumed
        ticket is provided.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        pt.consume()
        self.assertRaises(InvalidTicketError, ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=self.valid_service)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``ProxyTicket.objects.delete_invalid_tickets()`` should
        only delete ``ProxyTicket``s that are either expired or consumed.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        expired_pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        expired_pt.created = now() - timedelta(minutes=pt.TICKET_EXPIRE + 1)
        expired_pt.save()
        consumed_pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        consumed_pt.consume()

        ProxyTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyTicket.objects.count(), 1)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=expired_pt.ticket)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=consumed_pt.ticket)

    def test_consume_tickets(self):
        """
        Calling ``ProxyTicket.objects.consume_tickets()`` should consume
        tickets belonging to the provided user.
        """
        pt1 = ProxyTicket.objects.create_ticket(**self.ticket_info)
        pt2 = ProxyTicket.objects.create_ticket(**self.ticket_info)

        ProxyTicket.objects.consume_tickets(self.user)
        self.assertEqual(ProxyTicket.objects.get(ticket=pt1).is_consumed(), True)
        self.assertEqual(ProxyTicket.objects.get(ticket=pt2).is_consumed(), True)

    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should only delete
        ``ProxyTicket``s that are either expired or consumed.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        expired_pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        expired_pt.created = now() - timedelta(minutes=pt.TICKET_EXPIRE + 1)
        expired_pt.save()
        consumed_pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        consumed_pt.consume()

        management.call_command('cleanupcas')
        self.assertEqual(ProxyTicket.objects.count(), 1)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=expired_pt.ticket)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=consumed_pt.ticket)


class ProxyGrantingTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyGrantingTicket``s.
    """
    valid_pgt_str = 'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_pgt_regexp = '^PGT-[0-9]{10,}-[a-zA-Z0-9]{32}$'
    valid_pgtiou_str = 'PGTIOU-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_pgtiou_regexp = '^PGTIOU-[0-9]{10,}-[a-zA-Z0-9]{32}$'
    valid_service = 'http://www.example.com/'
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    ticket_info = {}

    def setUp(self):
        """
        Create a test user for authentication purposes and update the ticket
        information dictionary with the created user.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({'user': self.user})

        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_create_ticket(self):
        """
        A new ``ProxyGrantingTicket`` ought to exist in the database with a
        valid ticket string, be neither consumed or expired and be related to
        the ``User`` that authorized its creation.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                        validate=False,
                                                        **self.ticket_info)

        self.assertEqual(ProxyGrantingTicket.objects.count(), 1)
        self.assertTrue(re.search(self.valid_pgt_regexp, pgt.ticket))
        self.assertTrue(re.search(self.valid_pgtiou_regexp, pgt.iou))
        self.assertFalse(pgt.is_consumed())
        self.assertFalse(pgt.is_expired())
        self.assertEqual(pgt.user, self.user)

    def test_validate_ticket(self):
        """
        ``validate_ticket()`` ought to return the correct ``ProxyGrantingTicket``
        when provided with a valid ticket string and data. The validation
        process should not consume the ``ProxyGrantingTicket``.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                        validate=False,
                                                        **self.ticket_info)
        self.assertTrue(ProxyGrantingTicket.objects.validate_ticket(pgt.ticket,
                                                                    service=self.valid_service), pgt)
        self.assertFalse(pgt.is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail when no ticket
        string is provided.
        """
        self.assertRaises(InvalidRequestError,
                          ProxyGrantingTicket.objects.validate_ticket,
                          False, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail when no service
        identifier is provided.
        """
        self.assertRaises(InvalidRequestError, ProxyGrantingTicket.objects.validate_ticket,
                          self.valid_pgt_str, service=None)

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail when an invalid
        ticket string is provided.
        """
        self.assertRaises(InvalidTicketError, ProxyGrantingTicket.objects.validate_ticket,
                          '12345', service=self.valid_service)

    def test_validate_ticket_nonexistent_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail when a ticket
        cannot be found in the database.
        """
        self.assertRaises(BadPGTError, ProxyGrantingTicket.objects.validate_ticket,
                          self.valid_pgt_str, service=self.valid_service)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail when a consumed
        ticket is provided.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                        validate=False,
                                                        **self.ticket_info)
        pgt.consume()
        self.assertRaises(InvalidTicketError, ProxyGrantingTicket.objects.validate_ticket,
                          pgt.ticket, service=self.valid_service)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``ProxyGrantingTicket.objects.delete_invalid_tickets()`` should
        only delete ``ProxyGrantingTicket``s that are either expired or consumed.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                        validate=False,
                                                        **self.ticket_info)
        expired_pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                                validate=False,
                                                                **self.ticket_info)
        expired_pgt.created = now() - timedelta(minutes=pgt.TICKET_EXPIRE + 1)
        expired_pgt.save()
        consumed_pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                                 validate=False,
                                                                 **self.ticket_info)
        consumed_pgt.consume()

        ProxyGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyGrantingTicket.objects.count(), 1)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist, ProxyGrantingTicket.objects.get,
                          ticket=expired_pgt.ticket)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist, ProxyGrantingTicket.objects.get,
                          ticket=consumed_pgt.ticket)

    def test_consume_tickets(self):
        """
        Calling ``ProxyGrantingTicket.objects.consume_tickets()`` should consume
        tickets belonging to the provided user.
        """
        pgt1 = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                         validate=False,
                                                         **self.ticket_info)
        pgt2 = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                         validate=False,
                                                         **self.ticket_info)

        ProxyGrantingTicket.objects.consume_tickets(self.user)
        self.assertEqual(ProxyGrantingTicket.objects.get(ticket=pgt1).is_consumed(), True)
        self.assertEqual(ProxyGrantingTicket.objects.get(ticket=pgt2).is_consumed(), True)

    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should only delete
        ``ProxyGrantingTicket``s that are either expired or consumed.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                        validate=False,
                                                        **self.ticket_info)
        expired_pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                                validate=False,
                                                                **self.ticket_info)
        expired_pgt.created = now() - timedelta(minutes=pgt.TICKET_EXPIRE + 1)
        expired_pgt.save()
        consumed_pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                                 validate=False,
                                                                 **self.ticket_info)
        consumed_pgt.consume()

        management.call_command('cleanupcas')
        self.assertEqual(ProxyGrantingTicket.objects.count(), 1)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist, ProxyGrantingTicket.objects.get,
                          ticket=expired_pgt.ticket)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist, ProxyGrantingTicket.objects.get,
                          ticket=consumed_pgt.ticket)
