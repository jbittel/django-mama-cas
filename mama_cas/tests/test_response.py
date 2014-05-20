from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings

from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from .utils import parse
from mama_cas.exceptions import InvalidTicket
from mama_cas.response import ValidationResponse
from mama_cas.response import ProxyResponse


class ValidationResponseTests(TestCase):
    """
    Test the ``ValidationResponse`` XML output.
    """
    def setUp(self):
        self.st = ServiceTicketFactory()
        self.pgt = ProxyGrantingTicketFactory()

    def test_validation_response_content_type(self):
        """
        A ``ValidationResponse`` should be set to the provided
        content type.
        """
        resp = ValidationResponse(context={'ticket': self.st, 'error': None},
                                  content_type='text/xml')
        self.assertEqual(resp.get('Content-Type'), 'text/xml')

    def test_validation_response_ticket(self):
        """
        When given a ticket, a ``ValidationResponse`` should return
        an authentication success with the authenticated user.
        """
        resp = ValidationResponse(context={'ticket': self.st, 'error': None},
                                  content_type='text/xml')
        user = parse(resp.content).find('./authenticationSuccess/user')
        self.assertIsNotNone(user)
        self.assertEqual(user.text, 'ellen')

    def test_validation_response_error(self):
        """
        When given an error, a ``ValidationResponse`` should return
        an authentication failure with the error code and text.
        """
        error = InvalidTicket('Testing Error')
        resp = ValidationResponse(context={'ticket': None, 'error': error},
                                  content_type='text/xml')
        failure = parse(resp.content).find('./authenticationFailure')
        self.assertIsNotNone(failure)
        self.assertEqual(failure.get('code'), 'INVALID_TICKET')
        self.assertEqual(failure.text, 'Testing Error')

    def test_validation_response_pgt(self):
        """
        When given a ``ProxyGrantingTicket``, a ``ValidationResponse``
        should include a proxy-granting ticket.
        """
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'pgt': self.pgt},
                                  content_type='text/xml')
        pgt = parse(resp.content).find('./authenticationSuccess/proxyGrantingTicket')
        self.assertIsNotNone(pgt)
        self.assertEqual(pgt.text, self.pgt.iou)

    def test_validation_response_proxies(self):
        """
        When given a list of proxies, a ``ValidationResponse`` should
        include the list with ordering retained.
        """
        proxy_list = ['https://proxy2/pgtUrl', 'https://proxy1/pgtUrl']
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'proxies': proxy_list},
                                  content_type='text/xml')
        proxies = parse(resp.content).find('./authenticationSuccess/proxies')
        self.assertIsNotNone(proxies)
        self.assertEqual(len(proxies.findall('proxy')), len(proxy_list))
        self.assertEqual(proxies[0].text, proxy_list[0])
        self.assertEqual(proxies[1].text, proxy_list[1])

    @override_settings(MAMA_CAS_ATTRIBUTE_FORMAT='jasig')
    def test_validation_response_jasig_attributes(self):
        """
        When given custom user attributes, a ``ValidationResponse``
        should include the attributes in the configured format.
        """
        attrs = {'givenName': 'Ellen', 'sn': 'Cohen', 'email': 'ellen@example.com'}
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'attributes': attrs},
                                  content_type='text/xml')
        attributes = parse(resp.content).find('./authenticationSuccess/attributes')
        self.assertIsNotNone(attributes)
        self.assertEqual(len(attributes), len(attrs))
        for child in attributes:
            self.assertTrue(child.tag in attrs)
            self.assertEqual(child.text, attrs[child.tag])
            # Ordering is not guaranteed, so remove attributes from
            # the dict as they are validated. When done, check if the
            # dict is empty to see if all attributes were matched.
            del attrs[child.tag]
        self.assertEqual(len(attrs), 0)

    @override_settings(MAMA_CAS_ATTRIBUTE_FORMAT='rubycas')
    def test_validation_response_rubycas_attributes(self):
        """
        When given custom user attributes, a ``ValidationResponse``
        should include the attributes in the configured format.
        """
        attrs = {'givenName': 'Ellen', 'sn': 'Cohen', 'email': 'ellen@example.com'}
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'attributes': attrs},
                                  content_type='text/xml')
        success = parse(resp.content).find('./authenticationSuccess')
        self.assertIsNotNone(success)
        # The authenticationSuccess tag should include a child for
        # each attribute, plus the user element
        self.assertEqual(len(success), len(attrs) + 1)
        for child in success:
            if child.tag == 'user':
                continue
            self.assertTrue(child.tag in attrs)
            self.assertEqual(child.text, attrs[child.tag])
            # Ordering is not guaranteed, so remove attributes from
            # the dict as they are validated. When done, check if the
            # dict is empty to see if all attributes were matched.
            del attrs[child.tag]
        self.assertEqual(len(attrs), 0)

    @override_settings(MAMA_CAS_ATTRIBUTE_FORMAT='namevalue')
    def test_validation_response_namevalue_attributes(self):
        """
        When given custom user attributes, a ``ValidationResponse``
        should include the attributes in the configured format.
        """
        attrs = {'givenName': 'Ellen', 'sn': 'Cohen', 'email': 'ellen@example.com'}
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'attributes': attrs},
                                  content_type='text/xml')
        success = parse(resp.content).find('./authenticationSuccess')
        self.assertIsNotNone(success)
        self.assertEqual(len(success.findall('attribute')), len(attrs))
        for elem in success.findall('attribute'):
            self.assertTrue(elem.get('name') in attrs)
            self.assertEqual(elem.get('value'), attrs[elem.get('name')])
            # Ordering is not guaranteed, so remove attributes from
            # the dict as they are validated. When done, check if the
            # dict is empty to see if all attributes were matched.
            del attrs[elem.get('name')]
        self.assertEqual(len(attrs), 0)

    @override_settings(MAMA_CAS_ATTRIBUTE_FORMAT='invalid')
    def test_validation_response_invalid_attribute_format(self):
        """
        Configuring an invalid attribute format should raise an
        ``ImproperlyConfigured`` exception.
        """
        attrs = {'givenName': 'Ellen', 'sn': 'Cohen', 'email': 'ellen@example.com'}
        with self.assertRaises(ImproperlyConfigured):
            ValidationResponse(context={'ticket': self.st, 'error': None,
                                        'attributes': attrs},
                               content_type='text/xml')


class ProxyResponseTests(TestCase):
    """
    Test the ``ProxyResponse`` XML output.
    """
    def setUp(self):
        self.st = ServiceTicketFactory()
        self.pgt = ProxyGrantingTicketFactory()
        self.pt = ProxyTicketFactory()

    def test_proxy_response_content_type(self):
        """
        A ``ProxyResponse`` should be set to the provided
        content type.
        """
        resp = ProxyResponse(context={'ticket': self.pt, 'error': None},
                             content_type='text/xml')
        self.assertEqual(resp.get('Content-Type'), 'text/xml')

    def test_proxy_response_ticket(self):
        """
        When given a ticket, a ``ProxyResponse`` should return a
        proxy request success with the proxy ticket.
        """
        resp = ProxyResponse(context={'ticket': self.pt, 'error': None},
                             content_type='text/xml')
        pt = parse(resp.content).find('./proxySuccess/proxyTicket')
        self.assertIsNotNone(pt)
        self.assertEqual(pt.text, self.pt.ticket)

    def test_proxy_response_error(self):
        """
        When given an error, a ``ProxyResponse`` should return a
        proxy request failure with the error code and text.
        """
        error = InvalidTicket('Testing Error')
        resp = ProxyResponse(context={'ticket': None, 'error': error},
                             content_type='text/xml')
        failure = parse(resp.content).find('./proxyFailure')
        self.assertIsNotNone(failure)
        self.assertEqual(failure.get('code'), 'INVALID_TICKET')
        self.assertEqual(failure.text, 'Testing Error')
