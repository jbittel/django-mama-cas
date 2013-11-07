from django.conf import settings
from django.test import TestCase

from mama_cas.utils import add_query_params
from mama_cas.utils import is_scheme_https
from mama_cas.utils import clean_service_url
from mama_cas.utils import is_valid_service_url


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
        the ``scheme`` and ``netloc`` components of the original URL.
        """
        url = 'http://www.example.com:8080/test?test3=blue#green'
        self.assertEqual('http://www.example.com:8080', clean_service_url(url))
        url = 'https://www.example.com/'
        self.assertEqual('https://www.example.com', clean_service_url(url))

    def test_is_valid_service_url(self):
        """
        When valid services are configured, ``is_valid_service_url()``
        should return ``True`` if the provided URL matches, and
        ``False`` otherwise.
        """
        old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com',)
        self.assertTrue(is_valid_service_url('http://www.example.com'))
        self.assertFalse(is_valid_service_url('http://www.example.org'))
        settings.MAMA_CAS_VALID_SERVICES = old_valid_services

    def test_empty_valid_services(self):
        """
        When no valid services are configured,
        ``is_valid_service_url()`` should simply return ``True``.
        """
        old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ()
        self.assertTrue(is_valid_service_url('http://www.example.com'))
        settings.MAMA_CAS_VALID_SERVICES = old_valid_services
