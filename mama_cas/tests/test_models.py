import re
from datetime import timedelta

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.utils.timezone import now

from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from .factories import UserFactory
from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket
from mama_cas.exceptions import BadPgt
from mama_cas.exceptions import InvalidRequest
from mama_cas.exceptions import InvalidService
from mama_cas.exceptions import InvalidTicket


class ServiceTicketTests(TestCase):
    """
    Test the model and manager used for ``ServiceTicket``s.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        self.user = UserFactory()

        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_create_ticket(self):
        """
        A new ``ServiceTicket`` ought to exist in the database with
        a valid ticket string, be neither consumed or expired and be
        related to the ``User`` that authorized its creation.
        """
        st = ServiceTicketFactory()

        self.assertEqual(ServiceTicket.objects.count(), 1)
        self.assertTrue(re.search('^ST-[0-9]{10,}-[a-zA-Z0-9]{32}$',
                                  st.ticket))
        self.assertFalse(st.is_consumed())
        self.assertFalse(st.is_expired())
        self.assertEqual(st.user, self.user)

    def test_validate_ticket(self):
        """
        Validation ought to return the correct ``ServiceTicket`` when
        provided with a valid ticket string and data. The validation
        process also ought to consume the ``ServiceTicket``.
        """
        st = ServiceTicketFactory()
        self.assertTrue(ServiceTicket.objects.validate_ticket(st.ticket,
                                                              self.service_url), st)
        self.assertTrue(ServiceTicket.objects.get(ticket=st.ticket).is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        no ticket string is provided.
        """
        self.assertRaises(InvalidRequest,
                          ServiceTicket.objects.validate_ticket, None, None)

    def test_validate_ticket_no_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail and
        consume the ticket when no service identifier is provided.
        """
        st = ServiceTicketFactory()
        self.assertRaises(InvalidRequest,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, None)
        self.assertTrue(ServiceTicket.objects.get(ticket=st.ticket).is_consumed())

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        an invalid ticket string is provided.
        """
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          '12345', self.service_url)

    def test_validate_ticket_unknown_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a ticket cannot be found in the database.
        """
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          self.service_url)

    def test_validate_ticket_invalid_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a service identifier is provided that does not match the
        ticket's service identifier.
        """
        st = ServiceTicketFactory()
        self.assertRaises(InvalidService,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, 'http://www.example.org/')

    def test_validate_ticket_invalid_service_origin(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        the service origin does not match the ticket's service origin.
        """
        st = ServiceTicketFactory()
        self.assertRaises(InvalidService,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, 'http://sub.example.com/')

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        an expired ticket is provided.
        """
        st = ServiceTicketFactory(expires=now() - timedelta(seconds=1))
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          st.ticket, self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a consumed ticket is provided.
        """
        st = ServiceTicketFactory()
        st.consume()
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          st.ticket, self.service_url)

    def test_validate_ticket_renew(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should succeed if the ticket was issued from
        the presentation of the user's primary credentials.
        """
        st = ServiceTicketFactory(primary=True)
        self.assertEqual(ServiceTicket.objects.validate_ticket(st.ticket,
                                                               self.service_url,
                                                               renew=True), st)

    def test_validate_ticket_renew_secondary(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should fail if the ticket was not issued
        from the presentation of the user's primary credentials.
        """
        st = ServiceTicketFactory()
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          st.ticket, self.service_url, renew=True)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ServiceTicket``s that are either expired or consumed.
        Invalid ``ServiceTicket``s that are referenced by
        ``ProxyGrantingTicket``s should not be deleted.
        """
        ServiceTicketFactory()
        expired = ServiceTicketFactory(expires=now() - timedelta(seconds=1))
        consumed = ServiceTicketFactory(consumed=now())
        referenced = ServiceTicketFactory(consumed=now())
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
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        st1 = ServiceTicketFactory()
        st2 = ServiceTicketFactory()
        ServiceTicket.objects.consume_tickets(self.user)

        self.assertTrue(ServiceTicket.objects.get(ticket=st1).is_consumed())
        self.assertTrue(ServiceTicket.objects.get(ticket=st2).is_consumed())


class ProxyTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyTicket``s.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        self.user = UserFactory()
        self.pgt = ProxyGrantingTicketFactory()

        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_create_ticket(self):
        """
        A new ``ProxyTicket`` ought to exist in the database with
        a valid ticket string, be neither consumed or expired and
        be related to the ``User`` and ``ProxyGrantingTicket`` that
        authorized its creation.
        """
        pt = ProxyTicketFactory(granted_by_pgt=self.pgt)
        self.assertEqual(ProxyTicket.objects.count(), 1)
        self.assertTrue(re.search('^PT-[0-9]{10,}-[a-zA-Z0-9]{32}$', pt.ticket))
        self.assertFalse(pt.is_consumed())
        self.assertFalse(pt.is_expired())
        self.assertEqual(pt.user, self.user)
        self.assertEqual(pt.granted_by_pgt, self.pgt)

    def test_validate_ticket(self):
        """
        Validation ought to return the correct ``ProxyTicket`` when
        provided with a valid ticket string and data. The validation
        process also ought to consume the ``ProxyTicket``.
        """
        pt = ProxyTicketFactory()
        self.assertTrue(ProxyTicket.objects.validate_ticket(pt.ticket,
                                                            self.service_url), pt)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt.ticket).is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        no ticket string is provided.
        """
        self.assertRaises(InvalidRequest, ProxyTicket.objects.validate_ticket,
                          None, None)

    def test_validate_ticket_no_service(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        no service identifier is provided and the ticket ought to
        be consumed.
        """
        pt = ProxyTicketFactory()
        self.assertRaises(InvalidRequest, ProxyTicket.objects.validate_ticket,
                          pt.ticket, None)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt.ticket).is_consumed())

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        an invalid ticket string is provided.
        """
        self.assertRaises(InvalidTicket, ProxyTicket.objects.validate_ticket,
                          '12345', self.service_url)

    def test_validate_ticket_unknown_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a ticket cannot be found in the database.
        """
        self.assertRaises(InvalidTicket, ProxyTicket.objects.validate_ticket,
                          'PT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          self.service_url)

    def test_validate_ticket_invalid_service(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a service identifier is provided that does not match the
        ticket's service identifier.
        """
        pt = ProxyTicketFactory()
        self.assertRaises(InvalidService, ProxyTicket.objects.validate_ticket,
                          pt.ticket, 'http://www.example.org/')

    def test_validate_ticket_invalid_service_origin(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        the service origin does not match the ticket's service origin.
        """
        pt = ProxyTicketFactory()
        self.assertRaises(InvalidService, ProxyTicket.objects.validate_ticket,
                          pt.ticket, 'http://sub.example.com/')

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        an expired ticket is provided.
        """
        pt = ProxyTicketFactory()
        pt.expires = now() - timedelta(seconds=1)
        pt.save()
        self.assertRaises(InvalidTicket, ProxyTicket.objects.validate_ticket,
                          pt.ticket, self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a consumed ticket is provided.
        """
        pt = ProxyTicketFactory(consumed=now())
        self.assertRaises(InvalidTicket, ProxyTicket.objects.validate_ticket,
                          pt.ticket, self.service_url)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ProxyTicket``s that are either expired or consumed.
        Invalid ``ProxyTicket``s that are referenced by
        ``ProxyGrantingTicket``s should not be deleted.
        """
        ProxyTicketFactory()
        expired = ProxyTicketFactory(expires=now() - timedelta(seconds=1))
        consumed = ProxyTicketFactory(consumed=now())
        referenced = ProxyTicketFactory(consumed=now())
        ProxyGrantingTicketFactory(granted_by_pt=referenced)

        ProxyTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyTicket.objects.count(), 2)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=expired.ticket)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=consumed.ticket)

    def test_consume_tickets(self):
        """
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        pt1 = ProxyTicketFactory()
        pt2 = ProxyTicketFactory()
        ProxyTicket.objects.consume_tickets(self.user)

        self.assertTrue(ProxyTicket.objects.get(ticket=pt1).is_consumed())
        self.assertTrue(ProxyTicket.objects.get(ticket=pt2).is_consumed())


class ProxyGrantingTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyGrantingTicket``s.
    """
    pgt_url = 'http://www.example.com/'

    def setUp(self):
        self.user = UserFactory()

        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_create_ticket(self):
        """
        A new ``ProxyGrantingTicket`` ought to exist in the database
        with a valid ticket string, be neither consumed or expired and
        be related to the ``User`` that authorized its creation.
        """
        pgt = ProxyGrantingTicketFactory()
        self.assertEqual(ProxyGrantingTicket.objects.count(), 1)
        self.assertTrue(re.search('^PGT-[0-9]{10,}-[a-zA-Z0-9]{32}$',
                                  pgt.ticket))
        self.assertTrue(re.search('^PGTIOU-[0-9]{10,}-[a-zA-Z0-9]{32}$',
                                  pgt.iou))
        self.assertFalse(pgt.is_consumed())
        self.assertFalse(pgt.is_expired())
        self.assertEqual(pgt.user, self.user)

    def test_validate_ticket(self):
        """
        Validation ought to return the correct ``ProxyGrantingTicket``
        when provided with a valid ticket string and data. The
        validation process should not consume the
        ``ProxyGrantingTicket``.
        """
        pgt = ProxyGrantingTicketFactory()
        self.assertTrue(ProxyGrantingTicket.objects.validate_ticket(pgt.ticket,
                                                                    self.pgt_url), pgt)
        self.assertFalse(pgt.is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when no ticket string is provided.
        """
        self.assertRaises(InvalidRequest,
                          ProxyGrantingTicket.objects.validate_ticket,
                          False, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when no service identifier is provided.
        """
        self.assertRaises(InvalidRequest,
                          ProxyGrantingTicket.objects.validate_ticket,
                          'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          None)

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when an invalid ticket string is provided.
        """
        self.assertRaises(InvalidTicket,
                          ProxyGrantingTicket.objects.validate_ticket,
                          '12345', self.pgt_url)

    def test_validate_ticket_unknown_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when a ticket cannot be found in the database.
        """
        self.assertRaises(BadPgt, ProxyGrantingTicket.objects.validate_ticket,
                          'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          self.pgt_url)

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when an expired ticket is provided.
        """
        pgt = ProxyGrantingTicketFactory(expires=now() - timedelta(seconds=1))
        self.assertRaises(InvalidTicket,
                          ProxyGrantingTicket.objects.validate_ticket,
                          pgt.ticket, self.pgt_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when a consumed ticket is provided.
        """
        pgt = ProxyGrantingTicketFactory(consumed=now())
        self.assertRaises(InvalidTicket,
                          ProxyGrantingTicket.objects.validate_ticket,
                          pgt.ticket, self.pgt_url)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ProxyGrantingTicket``s that are either expired or consumed.
        ``ProxyGrantingTicket``s referenced by ``ProxyTicket``s
        should not be deleted.
        """
        ProxyGrantingTicketFactory()
        expired = ProxyGrantingTicketFactory(expires=now() - timedelta(seconds=1))
        consumed = ProxyGrantingTicketFactory(consumed=now())
        referenced = ProxyGrantingTicketFactory(consumed=now())
        ProxyTicketFactory(granted_by_pgt=referenced)

        ProxyGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyGrantingTicket.objects.count(), 2)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist,
                          ProxyGrantingTicket.objects.get,
                          ticket=expired.ticket)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist,
                          ProxyGrantingTicket.objects.get,
                          ticket=consumed.ticket)

    def test_consume_tickets(self):
        """
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        pgt1 = ProxyGrantingTicketFactory()
        pgt2 = ProxyGrantingTicketFactory()

        ProxyGrantingTicket.objects.consume_tickets(self.user)
        self.assertTrue(ProxyGrantingTicket.objects.get(ticket=pgt1).is_consumed())
        self.assertTrue(ProxyGrantingTicket.objects.get(ticket=pgt2).is_consumed())


class ManagementCommandTests(TestCase):
    """
    Test management commands that operate on ``Ticket``s.
    """
    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should delete ``Ticket``s
        that are either expired or consumed.
        """
        st = ServiceTicketFactory(consumed=now())
        pgt = ProxyGrantingTicketFactory(granted_by_st=st, consumed=now())
        ProxyTicketFactory(granted_by_pgt=pgt, consumed=now())

        management.call_command('cleanupcas')
        self.assertEqual(ServiceTicket.objects.count(), 0)
        self.assertEqual(ProxyGrantingTicket.objects.count(), 0)
        self.assertEqual(ProxyTicket.objects.count(), 0)
