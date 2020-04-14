from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import modify_settings
from django.test.utils import override_settings

from mama_cas.services import get_callbacks
from mama_cas.services import get_logout_url
from mama_cas.services import logout_allowed
from mama_cas.services import proxy_allowed
from mama_cas.services import proxy_callback_allowed
from mama_cas.services import service_allowed
from mama_cas.services.backends import services as cached_services


class ServicesTests(TestCase):
    def tearDown(self):
        try:
            # Remove cached property so the valid services
            # setting can be changed per-test
            del cached_services.services
        except AttributeError:
            pass

    def test_get_callbacks(self):
        """
        When callbacks are configured, ``get_callbacks()`` should return
        a list of the configured callbacks and an empty list otherwise.
        """
        self.assertEqual(get_callbacks('http://www.example.com'), ['mama_cas.callbacks.user_name_attributes'])
        self.assertEqual(get_callbacks('http://example.org'), [])

    def test_get_logout_url(self):
        """
        When a logout URL is configured, ``get_logout_url()`` should return
        the URL and ``None`` otherwise.
        """
        self.assertEqual(get_logout_url('http://www.example.com'), 'https://example.com/logout')
        self.assertIsNone(get_logout_url('http://example.org'))

    def test_logout_allowed(self):
        """
        When logout behavior is enabled, ``logout_allowed()`` should
        return ``True`` and ``False`` otherwise.
        """
        self.assertTrue(logout_allowed('http://www.example.com'))
        self.assertFalse(logout_allowed('http://example.com'))
        self.assertFalse(logout_allowed('http://www.example.org'))

    @modify_settings(MAMA_CAS_SERVICES={
        'append': [{'SERVICE': r'http://example\.org/proxy'}]
    })
    def test_proxy_allowed(self):
        """
        When proxy behavior is enabled, ``proxy_allowed()`` should
        return ``True`` and ``False`` otherwise. If it is not
        configured at all, ``True`` should be returned.
        """
        self.assertTrue(proxy_allowed('http://www.example.com'))
        self.assertTrue(proxy_allowed('http://example.org/proxy'))
        self.assertFalse(proxy_allowed('http://example.com'))
        self.assertFalse(proxy_allowed('http://www.example.org'))

    def test_proxy_callback_allowed(self):
        """
        When a proxy callback is configured, ``proxy_callback_allowed()``
        should return ``True`` if the pgturl matches the pattern and
        ``False`` otherwise.
        """
        self.assertTrue(proxy_callback_allowed('https://www.example.com', 'https://www.example.com'))
        self.assertFalse(proxy_callback_allowed('https://www.example.com', 'https://www.example.org'))
        self.assertFalse(proxy_callback_allowed('http://example.org', 'http://example.org'))

    @override_settings(MAMA_CAS_VALID_SERVICES=(r'http://.*\.example\.com',))
    def test_service_allowed_tuple(self):
        """
        When valid services are configured, ``service_allowed()``
        should return ``True`` if the provided URL matches, and
        ``False`` otherwise.
        """
        del settings.MAMA_CAS_SERVICES
        self.assertTrue(service_allowed('http://www.example.com'))
        self.assertFalse(service_allowed('http://www.example.org'))

    def test_service_allowed(self):
        """
        When valid services are configured, ``service_allowed()``
        should return ``True`` if the provided URL matches, and
        ``False`` otherwise.
        """
        self.assertTrue(service_allowed('http://www.example.com'))
        self.assertFalse(service_allowed('http://www.example.org'))

    @override_settings(MAMA_CAS_VALID_SERVICES=())
    def test_empty_valid_services_tuple(self):
        """
        When no valid services are configured,
        ``service_allowed()`` should return ``True``.
        """
        del settings.MAMA_CAS_SERVICES
        self.assertTrue(service_allowed('http://www.example.com'))

    @override_settings(MAMA_CAS_SERVICES=[])
    def test_empty_services(self):
        """
        When no valid services are configured,
        ``service_allowed()`` should return ``True``.
        """
        self.assertTrue(service_allowed('http://www.example.com'))

    @override_settings(MAMA_CAS_SERVICES=[{}])
    def test_invalid_services(self):
        """
        When invalid services are configured, ``service_allowed()``
        should raise ``ImproperlyConfigured``.
        """
        with self.assertRaises(ImproperlyConfigured):
            service_allowed('http://www.example.com')

    @override_settings(
        MAMA_CAS_SERVICE_BACKENDS=[
            'mama_cas.tests.backends.CustomTestServiceBackend'
        ]
    )
    def test_custom_backend(self):
        """
        Test that a custom service backend can be used
        """
        # CustomTestServiceBackend allows any service with 'test.com' in
        # addition to defined services
        self.assertFalse(service_allowed('http://www.foo.com'))
        self.assertTrue(service_allowed('http://www.example.com'))
        self.assertTrue(service_allowed('http://www.test.com'))

    @override_settings(
        MAMA_CAS_SERVICE_BACKENDS=[
            'mama_cas.tests.backends.CustomTestInvalidServiceBackend'
        ]
    )
    def test_invalid_custom_backend(self):
        """
        Test that a custom service backend without properly defined
        attributes raises ``NotImplementedError``
        """

        with self.assertRaises(NotImplementedError):
            service_allowed('http://www.example.com')

        with self.assertRaises(NotImplementedError):
            get_callbacks('http://www.example.com')

        with self.assertRaises(NotImplementedError):
            get_logout_url('http://www.example.com')

        with self.assertRaises(NotImplementedError):
            logout_allowed('http://www.example.com')

        with self.assertRaises(NotImplementedError):
            proxy_allowed('http://www.example.com')
