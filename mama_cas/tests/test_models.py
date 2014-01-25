import re
from datetime import timedelta

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.utils.timezone import now

from mama_cas.compat import get_user_model
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
        """
        Initialize the environment for each test.
        """
        user = get_user_model()
        self.user = user.objects.create_user('ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
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
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)

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
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
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
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
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
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
        self.assertRaises(InvalidService,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, 'http://www.example.org/')

    def test_validate_ticket_invalid_service_origin(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        the service origin does not match the ticket's service origin.
        """
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
        self.assertRaises(InvalidService,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, 'http://sub.example.com/')

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        an expired ticket is provided.
        """
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
        st.expires = now() - timedelta(seconds=1)
        st.save()
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          st.ticket, self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a consumed ticket is provided.
        """
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
        st.consume()
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          st.ticket, self.service_url)

    def test_validate_ticket_renew(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should succeed if the ticket was issued from
        the presentation of the user's primary credentials.
        """
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user,
                                                 primary=True)
        self.assertEqual(ServiceTicket.objects.validate_ticket(st.ticket,
                                                               self.service_url,
                                                               renew=True), st)

    def test_validate_ticket_renew_secondary(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should fail if the ticket was not issued
        from the presentation of the user's primary credentials.
        """
        st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                 user=self.user)
        self.assertRaises(InvalidTicket, ServiceTicket.objects.validate_ticket,
                          st.ticket, self.service_url, renew=True)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ServiceTicket``s that are either expired or consumed.
        Invalid ``ServiceTicket``s that are referenced by
        ``ProxyGrantingTicket``s should not be deleted.
        """
        ServiceTicket.objects.create_ticket(service=self.service_url,
                                            user=self.user)
        expired_st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                         user=self.user)
        expired_st.expires = now() - timedelta(seconds=1)
        expired_st.save()
        consumed_st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                          user=self.user)
        consumed_st.consume()

        invalid_st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                         user=self.user)
        invalid_st.consume()
        ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                  granted_by_st=invalid_st,
                                                  user=self.user,
                                                  validate=False)

        ServiceTicket.objects.delete_invalid_tickets()
        self.assertEqual(ServiceTicket.objects.count(), 2)
        self.assertRaises(ServiceTicket.DoesNotExist,
                          ServiceTicket.objects.get,
                          ticket=expired_st.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist,
                          ServiceTicket.objects.get,
                          ticket=consumed_st.ticket)

    def test_consume_tickets(self):
        """
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        st1 = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                  user=self.user)
        st2 = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                  user=self.user)

        ServiceTicket.objects.consume_tickets(self.user)
        self.assertTrue(ServiceTicket.objects.get(ticket=st1).is_consumed())
        self.assertTrue(ServiceTicket.objects.get(ticket=st2).is_consumed())


class ProxyTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyTicket``s.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        user = get_user_model()
        self.user = user.objects.create_user('ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                             validate=False,
                                                             user=self.user)
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
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
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
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
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
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
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
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
        self.assertRaises(InvalidService, ProxyTicket.objects.validate_ticket,
                          pt.ticket, 'http://www.example.org/')

    def test_validate_ticket_invalid_service_origin(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        the service origin does not match the ticket's service origin.
        """
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
        self.assertRaises(InvalidService, ProxyTicket.objects.validate_ticket,
                          pt.ticket, 'http://sub.example.com/')

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        an expired ticket is provided.
        """
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
        pt.expires = now() - timedelta(seconds=1)
        pt.save()
        self.assertRaises(InvalidTicket, ProxyTicket.objects.validate_ticket,
                          pt.ticket, self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a consumed ticket is provided.
        """
        pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                               user=self.user,
                                               granted_by_pgt=self.pgt)
        pt.consume()
        self.assertRaises(InvalidTicket, ProxyTicket.objects.validate_ticket,
                          pt.ticket, self.service_url)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ProxyTicket``s that are either expired or consumed.
        Invalid ``ProxyTicket``s that are referenced by
        ``ProxyGrantingTicket``s should not be deleted.
        """
        ProxyTicket.objects.create_ticket(service=self.service_url,
                                          user=self.user,
                                          granted_by_pgt=self.pgt)
        expired_pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                                       user=self.user,
                                                       granted_by_pgt=self.pgt)
        expired_pt.expires = now() - timedelta(seconds=1)
        expired_pt.save()
        consumed_pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                                        user=self.user,
                                                        granted_by_pgt=self.pgt)
        consumed_pt.consume()

        invalid_pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                                       user=self.user,
                                                       granted_by_pgt=self.pgt)
        invalid_pt.consume()
        ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                  granted_by_pt=invalid_pt,
                                                  user=self.user,
                                                  validate=False)

        ProxyTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyTicket.objects.count(), 2)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=expired_pt.ticket)
        self.assertRaises(ProxyTicket.DoesNotExist, ProxyTicket.objects.get,
                          ticket=consumed_pt.ticket)

    def test_consume_tickets(self):
        """
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        pt1 = ProxyTicket.objects.create_ticket(service=self.service_url,
                                                user=self.user,
                                                granted_by_pgt=self.pgt)
        pt2 = ProxyTicket.objects.create_ticket(service=self.service_url,
                                                user=self.user,
                                                granted_by_pgt=self.pgt)
        ProxyTicket.objects.consume_tickets(self.user)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt1).is_consumed())
        self.assertTrue(ProxyTicket.objects.get(ticket=pt2).is_consumed())


class ProxyGrantingTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyGrantingTicket``s.
    """
    pgt_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        user = get_user_model()
        self.user = user.objects.create_user('ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
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
        pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                        user=self.user,
                                                        validate=False)
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
        pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                        user=self.user,
                                                        validate=False)
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
        pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                        user=self.user,
                                                        validate=False)
        pgt.expires = now() - timedelta(seconds=1)
        pgt.save()
        self.assertRaises(InvalidTicket,
                          ProxyGrantingTicket.objects.validate_ticket,
                          pgt.ticket, self.pgt_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when a consumed ticket is provided.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                        user=self.user,
                                                        validate=False)
        pgt.consume()
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
        ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                  user=self.user,
                                                  validate=False)
        expired_pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                                user=self.user,
                                                                validate=False)
        expired_pgt.expires = now() - timedelta(seconds=1)
        expired_pgt.save()
        consumed_pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                                 user=self.user,
                                                                 validate=False)
        consumed_pgt.consume()

        invalid_pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                                user=self.user,
                                                                validate=False)
        invalid_pgt.consume()
        ProxyTicket.objects.create_ticket(service=self.pgt_url,
                                          granted_by_pgt=invalid_pgt,
                                          user=self.user)

        ProxyGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyGrantingTicket.objects.count(), 2)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist,
                          ProxyGrantingTicket.objects.get,
                          ticket=expired_pgt.ticket)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist,
                          ProxyGrantingTicket.objects.get,
                          ticket=consumed_pgt.ticket)

    def test_consume_tickets(self):
        """
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        pgt1 = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                         user=self.user,
                                                         validate=False)
        pgt2 = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                         user=self.user,
                                                         validate=False)

        ProxyGrantingTicket.objects.consume_tickets(self.user)
        self.assertTrue(ProxyGrantingTicket.objects.get(ticket=pgt1).is_consumed())
        self.assertTrue(ProxyGrantingTicket.objects.get(ticket=pgt2).is_consumed())


class ManagementCommandTests(TestCase):
    """
    Test management commands that operate on ``Ticket``s.
    """
    pgt_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        user = get_user_model()
        self.user = user.objects.create_user('ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')

    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should delete ``Ticket``s
        that are either expired or consumed.
        """
        st = ServiceTicket.objects.create_ticket(service=self.pgt_url,
                                                 user=self.user)
        st.consume()
        pgt = ProxyGrantingTicket.objects.create_ticket(self.pgt_url,
                                                        granted_by_st=st,
                                                        validate=False,
                                                        user=self.user)
        pgt.consume()
        pt = ProxyTicket.objects.create_ticket(service=self.pgt_url,
                                               granted_by_pgt=pgt,
                                               user=self.user)
        pt.consume()

        management.call_command('cleanupcas')
        self.assertEqual(ServiceTicket.objects.count(), 0)
        self.assertEqual(ProxyGrantingTicket.objects.count(), 0)
        self.assertEqual(ProxyTicket.objects.count(), 0)
