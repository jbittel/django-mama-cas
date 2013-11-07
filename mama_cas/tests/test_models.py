import re
from datetime import timedelta

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.utils.timezone import now
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:  # Django version < 1.5
    from django.contrib.auth.models import User

from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket
from mama_cas.exceptions import BadPGTError
from mama_cas.exceptions import InvalidRequestError
from mama_cas.exceptions import InvalidServiceError
from mama_cas.exceptions import InvalidTicketError


class ServiceTicketTests(TestCase):
    """
    Test the model and manager used for ``ServiceTicket``s.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(username='ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
        self.ticket_info = {'service': self.service_url, 'user': self.user}

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
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)

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
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertTrue(ServiceTicket.objects.validate_ticket(st.ticket,
                                                              service=self.service_url), st)
        self.assertTrue(ServiceTicket.objects.get(ticket=st.ticket).is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        no ticket string is provided.
        """
        self.assertRaises(InvalidRequestError,
                          ServiceTicket.objects.validate_ticket, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail and
        consume the ticket when no service identifier is provided.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidRequestError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service=None)
        self.assertTrue(ServiceTicket.objects.get(ticket=st.ticket).is_consumed())

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        an invalid ticket string is provided.
        """
        self.assertRaises(InvalidTicketError,
                          ServiceTicket.objects.validate_ticket,
                          '12345', service=self.service_url)

    def test_validate_ticket_unknown_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a ticket cannot be found in the database.
        """
        self.assertRaises(InvalidTicketError,
                          ServiceTicket.objects.validate_ticket,
                          'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          service=self.service_url)

    def test_validate_ticket_invalid_service(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a service identifier is provided that does not match the
        ticket's service identifier.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidServiceError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service='http://www.example.org/')

    def test_validate_ticket_invalid_service_origin(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        the service origin does not match the ticket's service origin.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidServiceError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service='http://sub.example.com/')

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        an expired ticket is provided.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        st.created = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        st.save()
        self.assertRaises(InvalidTicketError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ServiceTicket`` validation process ought to fail when
        a consumed ticket is provided.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        st.consume()
        self.assertRaises(InvalidTicketError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.service_url)

    def test_validate_ticket_renew(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should succeed if the ticket was issued from
        the presentation of the user's primary credentials.
        """
        st = ServiceTicket.objects.create_ticket(primary=True,
                                                 **self.ticket_info)
        self.assertEqual(ServiceTicket.objects.validate_ticket(st.ticket,
                                                               service=self.service_url,
                                                               renew=True), st)

    def test_validate_ticket_renew_secondary(self):
        """
        When ``renew`` is set to ``True``, the ``ServiceTicket``
        validation process should fail if the ticket was not issued
        from the presentation of the user's primary credentials.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidTicketError,
                          ServiceTicket.objects.validate_ticket,
                          st.ticket, service=self.service_url, renew=True)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ServiceTicket``s that are either expired or consumed.
        """
        st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        expired_st.created = now() - timedelta(minutes=st.TICKET_EXPIRE + 1)
        expired_st.save()
        consumed_st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        consumed_st.consume()

        ServiceTicket.objects.delete_invalid_tickets()
        self.assertEqual(ServiceTicket.objects.count(), 1)
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
        st1 = ServiceTicket.objects.create_ticket(**self.ticket_info)
        st2 = ServiceTicket.objects.create_ticket(**self.ticket_info)

        ServiceTicket.objects.consume_tickets(self.user)
        self.assertTrue(ServiceTicket.objects.get(ticket=st1).is_consumed())
        self.assertTrue(ServiceTicket.objects.get(ticket=st2).is_consumed())

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
        self.assertRaises(ServiceTicket.DoesNotExist,
                          ServiceTicket.objects.get,
                          ticket=expired_st.ticket)
        self.assertRaises(ServiceTicket.DoesNotExist,
                          ServiceTicket.objects.get,
                          ticket=consumed_st.ticket)


class ProxyTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyTicket``s.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(username='ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                             validate=False,
                                                             user=self.user)
        self.ticket_info = {'service': self.service_url,
                            'user': self.user,
                            'granted_by_pgt': self.pgt}

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
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertEqual(ProxyTicket.objects.count(), 1)
        self.assertTrue(re.search('^PT-[0-9]{10,}-[a-zA-Z0-9]{32}$',
                                  pt.ticket))
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
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertTrue(ProxyTicket.objects.validate_ticket(pt.ticket,
                                                            service=self.service_url), pt)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt.ticket).is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        no ticket string is provided.
        """
        self.assertRaises(InvalidRequestError,
                          ProxyTicket.objects.validate_ticket, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        no service identifier is provided and the ticket ought to
        be consumed.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidRequestError,
                          ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=None)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt.ticket).is_consumed())

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        an invalid ticket string is provided.
        """
        self.assertRaises(InvalidTicketError, ProxyTicket.objects.validate_ticket,
                          '12345', service=self.service_url)

    def test_validate_ticket_unknown_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a ticket cannot be found in the database.
        """
        self.assertRaises(InvalidTicketError,
                          ProxyTicket.objects.validate_ticket,
                          'PT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          service=self.service_url)

    def test_validate_ticket_invalid_service(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a service identifier is provided that does not match the
        ticket's service identifier.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidServiceError,
                          ProxyTicket.objects.validate_ticket,
                          pt.ticket, service='http://www.example.org/')

    def test_validate_ticket_invalid_service_origin(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        the service origin does not match the ticket's service origin.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        self.assertRaises(InvalidServiceError,
                          ProxyTicket.objects.validate_ticket,
                          pt.ticket, service='http://sub.example.com/')

    def test_validate_ticket_expired_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        an expired ticket is provided.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        pt.created = now() - timedelta(minutes=pt.TICKET_EXPIRE + 1)
        pt.save()
        self.assertRaises(InvalidTicketError,
                          ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyTicket`` validation process ought to fail when
        a consumed ticket is provided.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        pt.consume()
        self.assertRaises(InvalidTicketError,
                          ProxyTicket.objects.validate_ticket,
                          pt.ticket, service=self.service_url)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ProxyTicket``s that are either expired or consumed.
        """
        pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        expired_pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        expired_pt.created = now() - timedelta(minutes=pt.TICKET_EXPIRE + 1)
        expired_pt.save()
        consumed_pt = ProxyTicket.objects.create_ticket(**self.ticket_info)
        consumed_pt.consume()

        ProxyTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyTicket.objects.count(), 1)
        self.assertRaises(ProxyTicket.DoesNotExist,
                          ProxyTicket.objects.get,
                          ticket=expired_pt.ticket)
        self.assertRaises(ProxyTicket.DoesNotExist,
                          ProxyTicket.objects.get,
                          ticket=consumed_pt.ticket)

    def test_consume_tickets(self):
        """
        Calling ``consume_tickets()`` should consume tickets belonging
        to the provided user.
        """
        pt1 = ProxyTicket.objects.create_ticket(**self.ticket_info)
        pt2 = ProxyTicket.objects.create_ticket(**self.ticket_info)

        ProxyTicket.objects.consume_tickets(self.user)
        self.assertTrue(ProxyTicket.objects.get(ticket=pt1).is_consumed())
        self.assertTrue(ProxyTicket.objects.get(ticket=pt2).is_consumed())

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
        self.assertRaises(ProxyTicket.DoesNotExist,
                          ProxyTicket.objects.get,
                          ticket=expired_pt.ticket)
        self.assertRaises(ProxyTicket.DoesNotExist,
                          ProxyTicket.objects.get,
                          ticket=consumed_pt.ticket)


class ProxyGrantingTicketTests(TestCase):
    """
    Test the model and manager used for ``ProxyGrantingTicket``s.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(username='ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
        self.ticket_info = {'user': self.user}

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
        pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                        validate=False,
                                                        **self.ticket_info)
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
        pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                        validate=False,
                                                        **self.ticket_info)
        self.assertTrue(ProxyGrantingTicket.objects.validate_ticket(pgt.ticket,
                                                                    service=self.service_url), pgt)
        self.assertFalse(pgt.is_consumed())

    def test_validate_ticket_no_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when no ticket string is provided.
        """
        self.assertRaises(InvalidRequestError,
                          ProxyGrantingTicket.objects.validate_ticket,
                          False, False)

    def test_validate_ticket_no_service(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when no service identifier is provided.
        """
        self.assertRaises(InvalidRequestError,
                          ProxyGrantingTicket.objects.validate_ticket,
                          'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          service=None)

    def test_validate_ticket_invalid_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when an invalid ticket string is provided.
        """
        self.assertRaises(InvalidTicketError,
                          ProxyGrantingTicket.objects.validate_ticket,
                          '12345', service=self.service_url)

    def test_validate_ticket_unknown_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when a ticket cannot be found in the database.
        """
        self.assertRaises(BadPGTError,
                          ProxyGrantingTicket.objects.validate_ticket,
                          'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          service=self.service_url)

    def test_validate_ticket_consumed_ticket(self):
        """
        The ``ProxyGrantingTicket`` validation process ought to fail
        when a consumed ticket is provided.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                        validate=False,
                                                        **self.ticket_info)
        pgt.consume()
        self.assertRaises(InvalidTicketError,
                          ProxyGrantingTicket.objects.validate_ticket,
                          pgt.ticket, service=self.service_url)

    def test_invalid_ticket_deletion(self):
        """
        Calling ``delete_invalid_tickets()`` should only delete
        ``ProxyGrantingTicket``s that are either expired or consumed.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                        validate=False,
                                                        **self.ticket_info)
        expired_pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                                validate=False,
                                                                **self.ticket_info)
        expired_pgt.created = now() - timedelta(minutes=pgt.TICKET_EXPIRE + 1)
        expired_pgt.save()
        consumed_pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                                 validate=False,
                                                                 **self.ticket_info)
        consumed_pgt.consume()

        ProxyGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(ProxyGrantingTicket.objects.count(), 1)
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
        pgt1 = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                         validate=False,
                                                         **self.ticket_info)
        pgt2 = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                         validate=False,
                                                         **self.ticket_info)

        ProxyGrantingTicket.objects.consume_tickets(self.user)
        self.assertTrue(ProxyGrantingTicket.objects.get(ticket=pgt1).is_consumed())
        self.assertTrue(ProxyGrantingTicket.objects.get(ticket=pgt2).is_consumed())

    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should only delete
        ``ProxyGrantingTicket``s that are either expired or consumed.
        """
        pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                        validate=False,
                                                        **self.ticket_info)
        expired_pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                                validate=False,
                                                                **self.ticket_info)
        expired_pgt.created = now() - timedelta(minutes=pgt.TICKET_EXPIRE + 1)
        expired_pgt.save()
        consumed_pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                                 validate=False,
                                                                 **self.ticket_info)
        consumed_pgt.consume()

        management.call_command('cleanupcas')
        self.assertEqual(ProxyGrantingTicket.objects.count(), 1)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist,
                          ProxyGrantingTicket.objects.get,
                          ticket=expired_pgt.ticket)
        self.assertRaises(ProxyGrantingTicket.DoesNotExist,
                          ProxyGrantingTicket.objects.get,
                          ticket=consumed_pgt.ticket)
