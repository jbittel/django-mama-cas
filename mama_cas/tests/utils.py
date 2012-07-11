import logging

from django.test import TestCase

from mama_cas.utils import is_scheme_https


logging.disable(logging.CRITICAL)


class UtilsTests(TestCase):
    def test_is_scheme_https(self):
        """
        When called with a URL, ``is_scheme_https`` should return True
        or False depending on the scheme of the parameter URL.
        """
        self.assertTrue(is_scheme_https('https://www.test.com/'))
        self.assertFalse(is_scheme_https('http://www.test.com/'))
