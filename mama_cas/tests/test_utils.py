# -*- coding: utf-8 -*-

from django.test import TestCase

from mama_cas.utils import add_query_params
from mama_cas.utils import clean_service_url
from mama_cas.utils import is_scheme_https
from mama_cas.utils import match_service
from mama_cas.utils import redirect
from mama_cas.utils import to_bool


class UtilsTests(TestCase):
    def test_add_query_params(self):
        """
        When called with a URL and a dict of parameters,
        ``add_query_params()`` should insert the parameters into the
        original URL.
        """
        url = 'http://www.example.com/?test3=blue'
        params = {'test1': 'red', 'test2': '', 'test3': 'indigo'}
        url = add_query_params(url, params)

        self.assertIn('test1=red', url)
        # Parameters with empty values should be ignored
        self.assertNotIn('test2=', url)
        # Existing parameters with the same name should be overwritten
        self.assertIn('test3=indigo', url)

    def test_add_query_params_unicode(self):
        """
        When Unicode parameters are provided, ``add_query_params()``
        should encode them appropriately.
        """
        params = {'unicode1': u'ä', u'unicode²': 'b'}
        url = add_query_params('http://www.example.com/', params)
        self.assertIn('unicode1=%C3%A4', url)
        self.assertIn('unicode%C2%B2=b', url)

    def test_is_scheme_https(self):
        """
        When called with a URL, ``is_scheme_https()`` should return
        ``True`` if the scheme is HTTPS, and ``False`` otherwise.
        """
        self.assertTrue(is_scheme_https('https://www.example.com/'))
        self.assertFalse(is_scheme_https('http://www.example.com/'))

    def test_clean_service_url(self):
        """
        When called with a URL, ``clean_service_url()`` should return
        the ``scheme``, ``netloc`` and ``path`` components of the URL.
        """
        url = 'http://www.example.com/test?test3=blue#green'
        self.assertEqual('http://www.example.com/test', clean_service_url(url))
        url = 'https://example.com:9443/'
        self.assertEqual('https://example.com:9443/', clean_service_url(url))

    def test_match_service(self):
        """
        When called with two service URLs, ``match_service()`` should return
        ``True`` if the ``scheme``, ``netloc`` and ``path`` components match
        and ``False`` otherwise.
        """
        self.assertTrue(match_service('https://www.example.com:80/', 'https://www.example.com:80/'))
        self.assertFalse(match_service('https://www.example.com:80/', 'https://www.example.com/'))
        self.assertFalse(match_service('https://www.example.com', 'https://www.example.com/'))

    def test_redirect(self):
        """
        When redirecting, params should be injected on the redirection
        URL.
        """
        r = redirect('http://www.example.com', params={'test1': 'red'})
        self.assertEqual('http://www.example.com?test1=red', r['Location'])
        r = redirect('cas_login', params={'test3': 'blue'})
        self.assertEqual('/login?test3=blue', r['Location'])

    def test_redirect_no_params(self):
        """
        When redirecting, if no params are provided only the URL
        should be present.
        """
        r = redirect('http://www.example.com')
        self.assertEqual('http://www.example.com', r['Location'])
        r = redirect('cas_login')
        self.assertEqual('/login', r['Location'])

    def test_redirect_invalid(self):
        """
        A non-URL that does not match a view name should raise the
        appropriate exception.
        """
        r = redirect('http')
        self.assertEqual('/login', r['Location'])

    def test_to_bool(self):
        """
        Any string value should evaluate as ``True``. Empty strings
        or strings of whitespace should evaluate as ``False``.
        """
        self.assertTrue(to_bool('true'))
        self.assertTrue(to_bool('1'))
        self.assertFalse(to_bool(None))
        self.assertFalse(to_bool(''))
        self.assertFalse(to_bool('   '))
