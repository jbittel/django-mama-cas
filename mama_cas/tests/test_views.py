from __future__ import unicode_literals

import unittest

try:
    from urllib.parse import quote
except ImportError:  # pragma: no cover
    from urllib import quote

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:  # Django version < 1.5
    from django.contrib.auth.models import User

from mama_cas.forms import LoginForm
from mama_cas.forms import LoginFormWarn
from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket


XMLNS = '{http://www.yale.edu/tp/cas}'


class LoginViewTests(TestCase):
    """
    Test the ``LoginView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_login_view(self):
        """
        When called with no parameters, a ``GET`` request to the view
        should display the correct template with a login form.
        """
        response = self.client.get(reverse('cas_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mama_cas/login.html')
        self.assertTrue(isinstance(response.context['form'], LoginForm))

    def test_login_view_cache(self):
        """
        A response from the view should contain the correct cache-
        control header.
        """
        response = self.client.get(reverse('cas_login'))
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_login_view_login(self):
        """
        When called with a valid username and password and no service,
        a ``POST`` request to the view should authenticate and login
        the user, and redirect to the correct view.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        self.assertEqual(self.client.session['_auth_user_id'], self.user.pk)
        self.assertRedirects(response, reverse('cas_login'))

    def test_login_view_login_service(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view with the ``service`` parameter set should create a
        ``ServiceTicket`` and redirect to the supplied service URL
        with the ticket included.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        query_str = "?service=%s" % quote(self.service_url, '')
        response = self.client.get(reverse('cas_login') + query_str)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        st = ServiceTicket.objects.latest('id')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(self.service_url))
        self.assertTrue(st.ticket in response['Location'])

    def test_login_view_login_post(self):
        """
        When called with a valid username, password and service, a
        ``POST`` request to the view should authenticate and login the
        user, create a ``ServiceTicket`` and redirect to the supplied
        service URL with the ticket included.
        """
        params = self.user_info.copy()
        params.update({'service': self.service_url})
        response = self.client.post(reverse('cas_login'), params)
        self.assertEqual(self.client.session['_auth_user_id'], self.user.pk)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        st = ServiceTicket.objects.latest('id')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(self.service_url))
        self.assertTrue(st.ticket in response['Location'])

    def test_login_view_renew(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view with the ``renew`` parameter set should log the user out
        and redirect them to the login page.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        response = self.client.get(reverse('cas_login') + '?renew=true')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(response, reverse('cas_login'))

    def test_login_view_gateway(self):
        """
        When called without a logged in user, a ``GET`` request to the
        view with the ``gateway`` and ``service`` parameters set
        should simply redirect the user to the supplied service URL.
        """
        query_str = "?gateway=true&service=%s" % quote(self.service_url, '')
        response = self.client.get(reverse('cas_login') + query_str)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.service_url)

    def test_login_view_gateway_auth(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view with the ``gateway`` and ``service`` parameters set
        should create a ``ServiceTicket`` and redirect to the supplied
        service URL with the ticket included.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        query_str = "?gateway=true&service=%s" % quote(self.service_url, '')
        response = self.client.get(reverse('cas_login') + query_str)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        st = ServiceTicket.objects.latest('id')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(self.service_url))
        self.assertTrue(st.ticket in response['Location'])


class WarnViewTests(TestCase):
    """
    Test the ``WarnView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_warn_view(self):
        """
        When called with no parameters and no logged in user, a ``GET``
        request to the view should simply redirect to the login view.
        """
        response = self.client.get(reverse('cas_warn'))
        self.assertRedirects(response, reverse('cas_login'))
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_warn_view_redirect(self):
        """
        When a user logs in with the warn parameter present, the user's
        session should contain a ``warn`` attribute and a
        ``ServiceTicket`` request to the credential requestor should
        redirect to the warn view.
        """
        response = self.client.get(reverse('cas_login'))
        # Only continue the test if the required form class is in use
        if isinstance(response.context['form'], LoginFormWarn):
            form_data = self.user_info.copy()
            form_data.update({'warn': 'true'})
            response = self.client.post(reverse('cas_login'), form_data)
            query_str = "?service=%s" % quote(self.service_url, '')
            response = self.client.get(reverse('cas_login') + query_str)
            self.assertEqual(self.client.session.get('warn'), True)
            self.assertRedirects(response, reverse('cas_warn') + query_str)

    def test_warn_view_display(self):
        """
        When called with a logged in user, a request to the warn view
        should display the correct template containing the provided
        service string.
        """
        self.client.login(username=self.user_info['username'],
                          password=self.user_info['password'])
        query_str = "?service=%s" % quote(self.service_url, '')
        response = self.client.get(reverse('cas_warn') + query_str)
        self.assertContains(response, self.service_url)
        self.assertTemplateUsed(response, 'mama_cas/warn.html')

    def test_warn_view_warned(self):
        """
        When a logged in user submits the form on the warn view, the
        user should be redirected to the login view with the ``warned``
        parameter present.
        """
        self.client.login(username=self.user_info['username'],
                          password=self.user_info['password'])
        response = self.client.post(reverse('cas_warn'))
        self.assertRedirects(response, reverse('cas_login') + '?warned=true')


class LogoutViewTests(TestCase):
    """
    Test the ``LogoutView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('.*\.example\.com',)
        self.old_follow_url = getattr(settings,
                                      'MAMA_CAS_FOLLOW_LOGOUT_URL', False)
        settings.MAMA_CAS_FOLLOW_LOGOUT_URL = False

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services
        settings.MAMA_CAS_FOLLOW_LOGOUT_URL = self.old_follow_url

    def test_logout_view(self):
        """
        When called with no parameters and no logged in user, a ``GET``
        request to the view should simply redirect to the login view.
        """
        response = self.client.get(reverse('cas_logout'))
        self.assertRedirects(response, reverse('cas_login'))
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_logout_view_post(self):
        """
        A ``POST`` request to the view should return an error that the
        method is not allowed.
        """
        response = self.client.post(reverse('cas_logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_view_success(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view should log the user out and display the correct template.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        query_str = '?url=http://www.example.com'
        response = self.client.get(reverse('cas_logout') + query_str)
        self.assertRedirects(response, reverse('cas_login'))
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_logout_view_follow_url(self):
        """
        When called with a logged in user and MAMA_CAS_FOLLOW_LOGOUT_URL
        is set to ``True``, a ``GET`` request to the view should log the
        user out and redirect to the supplied URL.
        """
        settings.MAMA_CAS_FOLLOW_LOGOUT_URL = True

        response = self.client.post(reverse('cas_login'), self.user_info)
        query_str = '?url=http://www.example.com'
        response = self.client.get(reverse('cas_logout') + query_str)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://www.example.com')
        self.assertFalse('_auth_user_id' in self.client.session)


class ValidateViewTests(TestCase):
    """
    Test the ``ValidateView`` view.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user('ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
        self.st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                      user=self.user)

        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view
        should return a validation failure.
        """
        response = self.client.get(reverse('cas_validate'))
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_validate_view_post(self):
        """
        A ``POST`` request to the view should return an error that the
        method is not allowed.
        """
        response = self.client.post(reverse('cas_validate'))
        self.assertEqual(response.status_code, 405)

    def test_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % ('http://www.example.org/',
                                               self.st.ticket)
        response = self.client.get(reverse('cas_validate') + query_str)
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                    'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        response = self.client.get(reverse('cas_validate') + query_str)
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the
        view should return a validation success and the service ticket
        should be consumed and invalid for future validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_validate') + query_str)
        self.assertContains(response, "yes\nellen\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

        # This should not validate as the ticket was consumed in the
        # preceeding request
        response = self.client.get(reverse('cas_validate') + query_str)
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')


class ServiceValidateViewTests(TestCase):
    """
    Test the ``ServiceValidateView`` view.
    """
    service_url = 'http://www.example.com/'
    pgt_url = 'https://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user('ellen',
                                             email='ellen@example.com',
                                             password='mamas&papas')
        self.user.first_name = 'Ellen'
        self.user.last_name = 'Cohen'
        self.user.save()
        self.st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                      user=self.user)

        self.old_user_attributes = getattr(settings,
                                           'MAMA_CAS_USER_ATTRIBUTES', {})
        settings.MAMA_CAS_USER_ATTRIBUTES = {'givenName': 'first_name',
                                             'sn': 'last_name',
                                             'email': 'email',
                                             'test': 'invalid'}
        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_USER_ATTRIBUTES = self.old_user_attributes
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_service_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view
        should return a validation failure.
        """
        response = self.client.get(reverse('cas_service_validate'))
        self.assertContains(response, 'INVALID_REQUEST')

    def test_service_validate_view_post(self):
        """
        A ``POST`` request to the view should return an error that the
        method is not allowed.
        """
        response = self.client.post(reverse('cas_service_validate'))
        self.assertEqual(response.status_code, 405)

    def test_service_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % ('http://www.example.org/',
                                               self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'INVALID_SERVICE')

    def test_service_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                    'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'INVALID_TICKET')

    def test_service_validate_view_proxy_ticket(self):
        """
        When passed a proxy ticket, the error should explain that
        validation failed because a proxy ticket was provided.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                    'PT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'INVALID_TICKET')
        self.assertContains(response, 'Proxy tickets cannot be validated'
                                      ' with /serviceValidate')

    def test_service_validate_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the
        view should return a validation success and the
        ``ServiceTicket`` should be consumed and invalid for future
        validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        # This should not validate as the ticket was consumed in the
        # preceeding request
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'INVALID_TICKET')

    @unittest.skipIf(pgt_url == 'https://www.example.com/',
                     'set pgt_url to a valid HTTPS URL')
    def test_service_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter,
        a ``GET`` request to the view should return a validation
        success and also attempt to create a ``ProxyGrantingTicket``.

        NOTE: this test will fail unless ``pgt_url`` is configured with
        a valid proxy callback URL.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.service_url,
                                                         self.st.ticket,
                                                         self.pgt_url)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertContains(response, 'proxyGrantingTicket')

    def test_service_validate_view_pgturl_http(self):
        """
        When called with correct parameters and an invalid HTTP
        ``pgtUrl`` parameter, a ``GET`` request to the view should
        return a validation success with no ``ProxyGrantingTicket``.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.service_url,
                                                         self.st.ticket,
                                                         'http://www.example.com/')
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertNotContains(response, 'proxyGrantingTicket')

    def test_service_validate_view_user_attributes(self):
        """
        When ``MAMA_CAS_USER_ATTRIBUTES`` is defined in the settings
        file, a service validation success should include the list of
        configured user attributes.
        """
        attr_format = getattr(settings, 'MAMA_CAS_ATTRIBUTE_FORMAT', 'jasig')
        settings.MAMA_CAS_ATTRIBUTE_FORMAT = 'jasig'
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'attributes')
        settings.MAMA_CAS_ATTRIBUTE_FORMAT = attr_format

    def test_service_validate_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined in the settings
        file, a service string should be checked against the list of
        valid services. If it does not match, a service authentication
        failure should be returned.
        """
        query_str = "?service=%s&ticket=%s" % ('http://www.example.org/',
                                               self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'INVALID_SERVICE')


class ProxyValidateViewTests(TestCase):
    """
    Test the ``ProxyValidateView`` view.
    """
    service_url = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    pgt_url = 'https://www.example.com/'

    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user('ellen',
                                             email='ellen@example.com',
                                             password='mamas&papas')
        self.userfirst_name = 'Ellen'
        self.user.last_name = 'Cohen'
        self.user.save()
        self.st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                      user=self.user)
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                             validate=False,
                                                             user=self.user,
                                                             granted_by_st=self.st)
        self.pt = ProxyTicket.objects.create_ticket(service=self.service_url,
                                                    user=self.user,
                                                    granted_by_pgt=self.pgt)

        self.old_user_attributes = getattr(settings,
                                           'MAMA_CAS_USER_ATTRIBUTES', {})
        settings.MAMA_CAS_USER_ATTRIBUTES = {'givenName': 'first_name',
                                             'sn': 'last_name',
                                             'email': 'email',
                                             'test': 'invalid'}
        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        settings.MAMA_CAS_USER_ATTRIBUTES = self.old_user_attributes
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_proxy_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view
        should return a validation failure.
        """
        response = self.client.get(reverse('cas_proxy_validate'))
        self.assertContains(response, 'INVALID_REQUEST')

    def test_proxy_validate_view_post(self):
        """
        A ``POST`` request to the view should return an error that the
        method is not allowed.
        """
        response = self.client.post(reverse('cas_proxy_validate'))
        self.assertEqual(response.status_code, 405)

    def test_proxy_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service,
                                               self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'INVALID_SERVICE')

    def test_proxy_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                    'PT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'INVALID_TICKET')

    def test_proxy_validate_view_st_success(self):
        """
        When called with a valid ``ServiceTicket``, a ``GET`` request
        to the view should return a validation success and the
        ``ServiceTicket`` should be consumed and invalid for future
        validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        # This should not validate as the ticket was consumed in the
        # preceeding request
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'INVALID_TICKET')

    def test_proxy_validate_view_pt_success(self):
        """
        When called with a valid ``ProxyTicket``, a ``GET`` request to
        the view should return a validation success and the
        ``ProxyTicket`` should be consumed and invalid for future
        validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertContains(response, 'http://www.example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        # This second validation request attempt should fail as the
        # ticket was consumed in the preceeding request
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'INVALID_TICKET')
        self.assertNotContains(response, 'http://www.example.com')

    def test_proxy_validate_view_proxies(self):
        """
        When a successful ``ProxyTicket`` validation occurs, the
        response should include a ``proxies`` block containing all of
        the proxies involved. When authentication has proceeded through
        multiple proxies, they must be listed in reverse order of being
        accessed.
        """
        pgt2 = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                         user=self.user,
                                                         granted_by_pt=self.pt,
                                                         validate=False)
        pt2 = ProxyTicket.objects.create_ticket(service='http://ww2.example.com',
                                                user=self.user,
                                                granted_by_pgt=pgt2)
        query_str = "?service=%s&ticket=%s" % ('http://ww2.example.com/', pt2)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertContains(response, 'http://ww2.example.com')
        self.assertContains(response, 'http://www.example.com')

    @unittest.skipIf(pgt_url == 'https://www.example.com/',
                     'set pgt_url to a valid HTTPS URL')
    def test_proxy_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter,
        a ``GET`` request to the view should return a validation
        success and also attempt to create a ``ProxyGrantingTicket``.

        NOTE: this test will fail unless ``pgt_url`` is configured with
        a valid proxy callback URL.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.service_url,
                                                         self.pt.ticket,
                                                         self.pgt_url)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertContains(response, 'proxyGrantingTicket')

    def test_proxy_validate_view_pgturl_http(self):
        """
        When called with correct parameters and an invalid HTTP
        ``pgtUrl`` parameter, a ``GET`` request to the view should
        return a validation success with no ``ProxyGrantingTicket``.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.service_url,
                                                         self.pt.ticket,
                                                         'http://www.example.com/')
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertNotContains(response, 'proxyGrantingTicket')

    def test_proxy_validate_view_user_attributes(self):
        """
        When ``MAMA_CAS_USER_ATTRIBUTES`` is defined in the settings
        file, a proxy validation success should include the list of
        configured user attributes.
        """
        attr_format = getattr(settings, 'MAMA_CAS_ATTRIBUTE_FORMAT', 'jasig')
        settings.MAMA_CAS_ATTRIBUTE_FORMAT = 'jasig'
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'attributes')
        settings.MAMA_CAS_ATTRIBUTE_FORMAT = attr_format

    def test_proxy_validate_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined in the settings
        file, a service string should be checked against the list of
        valid services. If it does not match, a proxy authentication
        failure should be returned.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service,
                                               self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'INVALID_SERVICE')


class ProxyViewTests(TestCase):
    """
    Test the ``ProxyView`` view.
    """
    service_url = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'

    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user('ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')
        self.st = ServiceTicket.objects.create_ticket(service=self.service_url,
                                                      user=self.user)
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.service_url,
                                                             user=self.user,
                                                             granted_by_st=self.st,
                                                             validate=False)

        self.old_valid_services = getattr(settings,
                                          'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = ('http://.*\.example\.com/',)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_proxy_view(self):
        """
        When called with no parameters, a ``GET`` request to the view
        should return a validation failure.
        """
        response = self.client.get(reverse('cas_proxy'))
        self.assertContains(response, 'INVALID_REQUEST')

    def test_proxy_view_post(self):
        """
        A ``POST`` request to the view should return an error that the
        method is not allowed.
        """
        response = self.client.post(reverse('cas_proxy'))
        self.assertEqual(response.status_code, 405)

    def test_proxy_view_no_service(self):
        """
        When called with no service identifier, a ``GET`` request to
        the view should return a validation failure.
        """
        query_str = "?pgt=%s" % (self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        self.assertContains(response, 'INVALID_REQUEST')

    def test_proxy_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET``
        request to the view should return a validation failure.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.service_url,
                    'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        response = self.client.get(reverse('cas_proxy') + query_str)
        self.assertContains(response, 'BAD_PGT')

    def test_proxy_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the
        view should return a validation success with an included
        ``ProxyTicket``.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.service_url,
                                                  self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        self.assertContains(response, 'proxyTicket')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined in the settings
        file, a service string should be checked against the list of
        valid services. If it does not match, a proxy authentication
        failure should be returned.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.invalid_service,
                                                  self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        self.assertContains(response, 'INVALID_SERVICE')
