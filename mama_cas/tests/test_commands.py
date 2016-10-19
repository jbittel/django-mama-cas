from django.core import management
from django.test import TestCase
from django.utils import six

from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket


class ManagementCommandTests(TestCase):
    """
    Test management commands that operate on tickets.
    """
    def test_cleanupcas_management_command(self):
        """
        The ``cleanupcas`` management command should delete tickets
        that are expired or consumed.
        """
        st = ServiceTicketFactory(consume=True)
        pgt = ProxyGrantingTicketFactory(expire=True, granted_by_st=st)
        ProxyTicketFactory(consume=True, granted_by_pgt=pgt)
        management.call_command('cleanupcas')

        self.assertEqual(ServiceTicket.objects.count(), 0)
        self.assertEqual(ProxyGrantingTicket.objects.count(), 0)
        self.assertEqual(ProxyTicket.objects.count(), 0)

    def test_cleanupcas_management_command_chain(self):
        """
        The ``cleanupcas`` management command should delete chains of
        invalid tickets.
        """
        st = ServiceTicketFactory(consume=True)
        pgt = ProxyGrantingTicketFactory(expire=True, granted_by_st=st)
        pt = ProxyTicketFactory(consume=True, granted_by_pgt=pgt)
        pgt2 = ProxyGrantingTicketFactory(expire=True, granted_by_st=None, granted_by_pt=pt)
        ProxyTicketFactory(consume=True, granted_by_pgt=pgt2)
        management.call_command('cleanupcas')

        self.assertEqual(ServiceTicket.objects.count(), 0)
        self.assertEqual(ProxyGrantingTicket.objects.count(), 0)
        self.assertEqual(ProxyTicket.objects.count(), 0)

    def test_checkservice_management_command(self):
        output = six.StringIO()
        management.call_command('checkservice', 'https://www.example.com', no_color=True, stdout=output)
        self.assertIn('Valid service', output.getvalue())

    def test_checkservice_management_command_invalid(self):
        output = six.StringIO()
        management.call_command('checkservice', 'https://example.org', no_color=True, stdout=output)
        self.assertIn('Invalid service', output.getvalue())
