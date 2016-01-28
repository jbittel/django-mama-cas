from __future__ import unicode_literals

from django.test import TestCase

from .factories import ServiceTicketFactory
from .utils import parse
from mama_cas.request import SingleSignOutRequest


class SingleSignOutRequestTests(TestCase):
    """
    Test the ``SingleSignOutRequest`` SAML output.
    """
    def setUp(self):
        self.st = ServiceTicketFactory()

    def test_sso_request(self):
        """
        A ``SingleSignOutRequest`` should contain the ticket string
        from the provided context.
        """
        content = SingleSignOutRequest(context={'ticket': self.st}).render_content()
        session_index = parse(content).find('./SessionIndex')
        self.assertIsNotNone(session_index)
        self.assertEqual(session_index.text, self.st.ticket)
