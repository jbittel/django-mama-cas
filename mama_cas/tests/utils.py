import logging

from django.test import TestCase

from mama_cas.utils import add_query_params
from mama_cas.utils import is_scheme_https


logging.disable(logging.CRITICAL)


class UtilsTests(TestCase):
    def test_add_query_params(self):
        """
        When called with a URL and a dict of parameters, ``add_query_params()``
        should insert the parameters into the existing URL.
        """
        url = 'http://www.example.com/?test3=blue'
        params = { 'test1': 'red', 'test2': '', 'test3': 'indigo' }
        url = add_query_params(url, params)

        self.assertIn('test1=red', url)
        # Parameters with empty values should be ignored
        self.assertNotIn('test2=', url)
        # Existing parameters with the same name should be overwritten
        self.assertIn('test3=indigo', url)

    def test_is_scheme_https(self):
        """
        When called with a URL, ``is_scheme_https()`` should return True
        or False depending on the scheme of the parameter URL.
        """
        self.assertTrue(is_scheme_https('https://www.example.com/'))
        self.assertFalse(is_scheme_https('http://www.example.com/'))
