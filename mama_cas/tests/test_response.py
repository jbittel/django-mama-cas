# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test import TestCase

from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from .utils import parse
from mama_cas.exceptions import InvalidTicket
from mama_cas.response import ValidationResponse
from mama_cas.response import ProxyResponse
from mama_cas.response import SamlValidationResponse


class ValidationResponseTests(TestCase):
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

    def test_validation_response_attributes(self):
        """
        When given custom user attributes, a ``ValidationResponse``
        should include the attributes in the response.
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

    def test_validation_response_nonstring_attributes(self):
        """
        When given non-string attributes, the values should be
        converted to strings in the response.
        """
        attrs = {'boolean': True}
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'attributes': attrs},
                                  content_type='text/xml')
        attributes = parse(resp.content).find('./authenticationSuccess/attributes')
        self.assertIsNotNone(attributes)
        self.assertEqual(attributes[0].tag, 'boolean')
        self.assertEqual(attributes[0].text, 'True')

    def test_validation_response_unicode_attributes(self):
        """
        When given Unicode attributes, the values should be
        handled correctly in the response.
        """
        attrs = {'unicode': u'тнє мαмαѕ & тнє ραραѕ'}
        resp = ValidationResponse(context={'ticket': self.st, 'error': None,
                                           'attributes': attrs},
                                  content_type='text/xml')
        attributes = parse(resp.content).find('./authenticationSuccess/attributes')
        self.assertIsNotNone(attributes)
        self.assertEqual(attributes[0].tag, 'unicode')
        self.assertEqual(attributes[0].text, 'тнє мαмαѕ & тнє ραραѕ')


class ProxyResponseTests(TestCase):
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


class SamlValidationResponseTests(TestCase):
    def setUp(self):
        self.st = ServiceTicketFactory(consume=True)

    def test_saml_validation_response_ticket(self):
        """
        When given a ticket, a ``SamlValidationResponse`` should return
        an authentication success.
        """
        resp = SamlValidationResponse(context={'ticket': self.st, 'error': None},
                                      content_type='text/xml')
        code = parse(resp.content).find('./Body/Response/Status/StatusCode')
        self.assertIsNotNone(code)
        self.assertEqual(code.get('Value'), 'samlp:Success')

    def test_saml_validation_response_error(self):
        """
        When given an error, a ``SamlValidationResponse`` should return
        an authentication failure with the error text.
        """
        error = InvalidTicket('Testing Error')
        resp = SamlValidationResponse(context={'ticket': None, 'error': error},
                                      content_type='text/xml')
        code = parse(resp.content).find('./Body/Response/Status/StatusCode')
        self.assertIsNotNone(code)
        self.assertEqual(code.get('Value'), 'samlp:RequestDenied')

        message = parse(resp.content).find('./Body/Response/Status/StatusMessage')
        self.assertIsNotNone(message)
        self.assertEqual(message.text, 'Testing Error')

    def test_saml_validation_response_attributes(self):
        """
        When given custom user attributes, a ``SamlValidationResponse``
        authentication success should include the attributes in the
        response.
        """
        attrs = {'givenName': 'Ellen', 'sn': 'Cohen', 'email': 'ellen@example.com'}
        resp = SamlValidationResponse(context={'ticket': self.st, 'error': None,
                                               'attributes': attrs},
                                      content_type='text/xml')
        attribute_statement = parse(resp.content).find('./Body/Response/Assertion/AttributeStatement')
        self.assertIsNotNone(attribute_statement)
        for attr in attribute_statement.findall('Attribute'):
            attr_name = attr.get('AttributeName')
            attr_value = attr.find('AttributeValue')
            self.assertTrue(attr_name in attrs)
            self.assertEqual(attr_value.text, attrs[attr_name])
            # Ordering is not guaranteed, so remove attributes from
            # the dict as they are validated. When done, check if the
            # dict is empty to see if all attributes were matched.
            del attrs[attr_name]
        self.assertEqual(len(attrs), 0)
