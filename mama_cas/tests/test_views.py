from __future__ import unicode_literals

from mock import patch

try:
    from urllib.parse import quote
except ImportError:  # pragma: no cover
    from urllib import quote

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from .factories import UserFactory
from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from .factories import ConsumedServiceTicketFactory
from mama_cas.forms import LoginForm
from mama_cas.models import ServiceTicket


class LoginViewTests(TestCase):
    """
    Test the ``LoginView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas'}
    warn_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'warn': 'on'}
    service_url = 'http://www.example.com/'

    def setUp(self):
        self.user = UserFactory()

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
        url = reverse('cas_login') + "?service=%s" % self.service_url
        response = self.client.post(url, self.user_info)
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

    @override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
    def test_login_view_warn_session(self):
        """
        When a user logs in with the warn parameter present, the user's
        session should contain a ``warn`` attribute.
        """
        self.client.post(reverse('cas_login'), self.warn_info)
        self.assertEqual(self.client.session.get('warn'), True)

    @override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
    def test_login_view_warn_auth_redirect(self):
        """
        When a logged in user requests a ``ServiceTicket`` and the
        ``warn`` attribute is set, it should redirect to the warn view
        with the appropriate parameters.
        """
        self.client.post(reverse('cas_login'), self.warn_info)
        quote_url = quote(self.service_url, '')
        query_str = "?service=%s" % quote_url
        response = self.client.get(reverse('cas_login') + query_str)
        self.assertTrue(reverse('cas_warn') in response['Location'])
        self.assertTrue("service=%s" % quote_url in response['Location'])
        self.assertTrue('ticket=ST-' in response['Location'])

    @override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
    def test_login_view_warn_auth_gateway_redirect(self):
        """
        When a logged in user requests a ``ServiceTicket`` with the
        gateway parameter and the ``warn`` attribute is set, it should
        redirect to the warn view with the appropriate parameters.
        """
        self.client.post(reverse('cas_login'), self.warn_info)
        quote_url = quote(self.service_url, '')
        query_str = "?gateway=true&service=%s" % quote_url
        response = self.client.get(reverse('cas_login') + query_str)
        self.assertTrue(reverse('cas_warn') in response['Location'])
        self.assertTrue("service=%s" % quote_url in response['Location'])
        self.assertTrue('ticket=ST-' in response['Location'])


@override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
class WarnViewTests(TestCase):
    """
    Test the ``WarnView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas'}
    url = 'http://www.example.com'

    def setUp(self):
        self.user = UserFactory()

    def test_warn_view_display(self):
        """
        When called with a logged in user, a request to the warn view
        should display the correct template containing the provided
        service string.
        """
        self.client.login(username=self.user_info['username'],
                          password=self.user_info['password'])
        st = ServiceTicketFactory()
        query_str = "?service=%s&ticket=%s" % (quote(self.url, ''), st.ticket)
        response = self.client.get(reverse('cas_warn') + query_str)
        self.assertContains(response, self.url, count=3)
        self.assertContains(response, st.ticket)
        self.assertTemplateUsed(response, 'mama_cas/warn.html')

    def test_warn_view_anonymous_user(self):
        """
        When a user is not logged in, a ``GET`` request to the view
        should redirect to the login view.
        """
        response = self.client.get(reverse('cas_warn'))
        self.assertRedirects(response, reverse('cas_login'))


@override_settings(MAMA_CAS_VALID_SERVICES=('.*\.example\.com',))
@override_settings(MAMA_CAS_FOLLOW_LOGOUT_URL=False)
class LogoutViewTests(TestCase):
    """
    Test the ``LogoutView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}

    def setUp(self):
        self.user = UserFactory()

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

    @override_settings(MAMA_CAS_FOLLOW_LOGOUT_URL=True)
    def test_logout_view_follow_url(self):
        """
        When called with a logged in user and MAMA_CAS_FOLLOW_LOGOUT_URL
        is set to ``True``, a ``GET`` request to the view should log the
        user out and redirect to the supplied URL.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        query_str = '?url=http://www.example.com'
        response = self.client.get(reverse('cas_logout') + query_str)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://www.example.com')
        self.assertFalse('_auth_user_id' in self.client.session)

    @override_settings(MAMA_CAS_ENABLE_SINGLE_SIGN_OUT=True)
    def test_logout_single_sign_out(self):
        """
        When called with a logged in user and MAMA_CAS_ENABLE_SINGLE_SIGN_OUT
        is set to ``True``, a ``GET`` request to the view should issue
        a POST request for each service accessed by the user.
        """
        ConsumedServiceTicketFactory()
        ConsumedServiceTicketFactory()
        self.client.post(reverse('cas_login'), self.user_info)
        query_str = '?url=http://www.example.com'
        with patch('requests.post') as mock:
            self.client.get(reverse('cas_logout') + query_str)
            self.assertEqual(mock.call_count, 2)


@override_settings(MAMA_CAS_VALID_SERVICES=('.*\.example\.com',))
class ValidateViewTests(TestCase):
    """
    Test the ``ValidateView`` view.
    """
    service_url = 'http://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()

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


@override_settings(MAMA_CAS_VALID_SERVICES=('.*\.example\.com',))
@override_settings(MAMA_CAS_USER_ATTRIBUTES={'givenName': 'first_name',
                                             'sn': 'last_name',
                                             'email': 'email',
                                             'test': 'invalid'})
class ServiceValidateViewTests(TestCase):
    """
    Test the ``ServiceValidateView`` view.
    """
    service_url = 'http://www.example.com/'
    pgt_url = 'https://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()

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

    def test_service_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter,
        a ``GET`` request to the view should return a validation
        success and also attempt to create a ``ProxyGrantingTicket``.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.service_url,
                                                         self.st.ticket,
                                                         self.pgt_url)
        url = reverse('cas_service_validate') + query_str
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            response = self.client.get(url)
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

    @override_settings(MAMA_CAS_ATTRIBUTE_FORMAT='jasig')
    def test_service_validate_view_user_attributes(self):
        """
        When ``MAMA_CAS_USER_ATTRIBUTES`` is defined in the settings
        file, a service validation success should include the list of
        configured user attributes.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, 'attributes')

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

    @override_settings(MAMA_CAS_ATTRIBUTES_CALLBACK='mama_cas.tests.callback.test_callback')
    def test_service_validate_view_attributes_callback(self):
        """
        When a custom callback is defined in the settings file, a service
        validation success should include the attributes that callback
        returns.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url, self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        self.assertContains(response, '<cas:username>ellen</cas:username>')


@override_settings(MAMA_CAS_VALID_SERVICES=('.*\.example\.com',))
@override_settings(MAMA_CAS_USER_ATTRIBUTES={'givenName': 'first_name',
                                             'sn': 'last_name',
                                             'email': 'email',
                                             'test': 'invalid'})
class ProxyValidateViewTests(TestCase):
    """
    Test the ``ProxyValidateView`` view.
    """
    service_url = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    pgt_url = 'https://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()
        self.pgt = ProxyGrantingTicketFactory()
        self.pt = ProxyTicketFactory()

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
        query_str = "?service=%s&ticket=%s" % (self.pt.service, self.pt.ticket)
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
        pgt2 = ProxyGrantingTicketFactory(granted_by_pt=self.pt,
                                          granted_by_st=None)
        pt2 = ProxyTicketFactory(service='http://ww2.example.com',
                                 granted_by_pgt=pgt2)
        query_str = "?service=%s&ticket=%s" % (pt2.service, pt2.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'ellen')
        self.assertContains(response, 'http://ww2.example.com')
        self.assertContains(response, 'http://www.example.com')

    def test_proxy_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter,
        a ``GET`` request to the view should return a validation
        success and also attempt to create a ``ProxyGrantingTicket``.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.service_url,
                                                         self.pt.ticket,
                                                         self.pgt_url)
        url = reverse('cas_proxy_validate') + query_str
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            response = self.client.get(url)
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

    @override_settings(MAMA_CAS_ATTRIBUTE_FORMAT='jasig')
    def test_proxy_validate_view_user_attributes(self):
        """
        When ``MAMA_CAS_USER_ATTRIBUTES`` is defined in the settings
        file, a proxy validation success should include the list of
        configured user attributes.
        """
        query_str = "?service=%s&ticket=%s" % (self.service_url,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        self.assertContains(response, 'attributes')

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
        self.st = ServiceTicketFactory()
        self.pgt = ProxyGrantingTicketFactory()

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

    @override_settings(MAMA_CAS_VALID_SERVICES=('.*\.example\.com',))
    def test_proxy_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined, a service string
        should be checked against the list of valid services. If it does
        not match, a proxy authentication failure should be returned.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.invalid_service,
                                                  self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        self.assertContains(response, 'INVALID_SERVICE')
