from __future__ import unicode_literals

from mock import patch

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from .factories import UserFactory
from .factories import ProxyGrantingTicketFactory
from .factories import ProxyTicketFactory
from .factories import ServiceTicketFactory
from .utils import build_url
from mama_cas.forms import LoginForm
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket
from mama_cas.request import SamlValidateRequest
from mama_cas.views import ProxyView
from mama_cas.views import ProxyValidateView
from mama_cas.views import ServiceValidateView
from mama_cas.views import ValidateView
from mama_cas.views import SamlValidateView


class LoginViewTests(TestCase):
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
        self.assertTrue('max-age=0' in response['Cache-Control'])

    def test_login_view_login(self):
        """
        When called with a valid username and password and no service,
        a ``POST`` request to the view should authenticate and login
        the user, and redirect to the correct view.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertRedirects(response, reverse('cas_login'))

    def test_login_view_login_service(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view with the ``service`` parameter set should create a
        ``ServiceTicket`` and redirect to the supplied service URL
        with the ticket included.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_login'), {'service': self.service_url})
        self.assertEqual(ServiceTicket.objects.count(), 1)
        st = ServiceTicket.objects.latest('id')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(self.service_url))
        self.assertTrue(st.ticket in response['Location'])

    def test_login_view_invalid_service(self):
        """
        When called with an invalid service URL, the view should
        return a 403 Forbidden response.
        """
        response = self.client.get(reverse('cas_login'), {'service': 'http://example.org', 'gateway': 'true'})
        self.assertEqual(response.status_code, 403)

    def test_login_view_login_post(self):
        """
        When called with a valid username, password and service, a
        ``POST`` request to the view should authenticate and login the
        user, create a ``ServiceTicket`` and redirect to the supplied
        service URL with the ticket included.
        """
        url = reverse('cas_login') + "?service=%s" % self.service_url
        response = self.client.post(url, self.user_info)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        st = ServiceTicket.objects.latest('id')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(self.service_url))
        self.assertTrue(st.ticket in response['Location'])

    def test_login_view_renew(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view with the ``renew`` parameter should display the login page.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_login'), {'service': self.service_url, 'renew': 'true'})
        self.assertTemplateUsed(response, 'mama_cas/login.html')

    def test_login_view_gateway(self):
        """
        When called without a logged in user, a ``GET`` request to the
        view with the ``gateway`` and ``service`` parameters set
        should simply redirect the user to the supplied service URL.
        """
        response = self.client.get(reverse('cas_login'), {'service': self.service_url, 'gateway': 'true'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.service_url)

    def test_login_view_gateway_auth(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view with the ``gateway`` and ``service`` parameters set
        should create a ``ServiceTicket`` and redirect to the supplied
        service URL with the ticket included.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_login'), {'service': self.service_url, 'gateway': 'true'})
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
        response = self.client.get(reverse('cas_login'), {'service': self.service_url})
        self.assertTrue(reverse('cas_warn') in response['Location'])
        self.assertTrue("service=" in response['Location'])
        self.assertTrue('ticket=ST-' in response['Location'])

    @override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
    def test_login_view_warn_auth_gateway_redirect(self):
        """
        When a logged in user requests a ``ServiceTicket`` with the
        gateway parameter and the ``warn`` attribute is set, it should
        redirect to the warn view with the appropriate parameters.
        """
        self.client.post(reverse('cas_login'), self.warn_info)
        response = self.client.get(reverse('cas_login'), {'service': self.service_url, 'gateway': 'true'})
        self.assertTrue(reverse('cas_warn') in response['Location'])
        self.assertTrue("service=" in response['Location'])
        self.assertTrue('ticket=ST-' in response['Location'])


@override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
class WarnViewTests(TestCase):
    user_info = {'username': 'ellen', 'password': 'mamas&papas'}

    def setUp(self):
        self.user = UserFactory()

    def test_warn_view_display(self):
        """
        When called with a logged in user, a request to the warn view
        should display the correct template containing the provided
        service string.
        """
        st = ServiceTicketFactory()
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_warn'), {'service': 'http://www.example.com', 'ticket': st.ticket})
        self.assertContains(response, 'http://www.example.com', count=3)
        self.assertContains(response, st.ticket)
        self.assertTemplateUsed(response, 'mama_cas/warn.html')

    def test_warn_view_anonymous_user(self):
        """
        When a user is not logged in, a request to the view should
        redirect to the login view.
        """
        response = self.client.get(reverse('cas_warn'))
        self.assertRedirects(response, reverse('cas_login'))

    def test_warn_view_invalid_service(self):
        """
        Whan in invalid service is provided, a request to the view
        should redirect to the login view.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_warn'), {'service': 'http://example.org'})
        self.assertRedirects(response, reverse('cas_login'))


@override_settings(MAMA_CAS_FOLLOW_LOGOUT_URL=False)
class LogoutViewTests(TestCase):
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    url = 'http://www.example.com'

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
        self.assertTrue('max-age=0' in response['Cache-Control'])

    def test_logout_view_success(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view should log the user out and display the correct template.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_logout'))
        self.assertRedirects(response, reverse('cas_login'))
        self.assertFalse('_auth_user_id' in self.client.session)

    @override_settings(MAMA_CAS_FOLLOW_LOGOUT_URL=True)
    def test_logout_view_follow_service(self):
        """
        When called with a logged in user and MAMA_CAS_FOLLOW_LOGOUT_URL
        is set to ``True``, a ``GET`` request containing ``service``
        should log the user out and redirect to the supplied URL.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_logout'), {'service': self.url})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.url)
        self.assertFalse('_auth_user_id' in self.client.session)

    @override_settings(MAMA_CAS_FOLLOW_LOGOUT_URL=True)
    def test_logout_view_follow_url(self):
        """
        When called with a logged in user and MAMA_CAS_FOLLOW_LOGOUT_URL
        is set to ``True``, a ``GET`` request containing ``url``
        should log the user out and redirect to the supplied URL.
        """
        self.client.login(**self.user_info)
        response = self.client.get(reverse('cas_logout'), {'url': self.url})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.url)
        self.assertFalse('_auth_user_id' in self.client.session)

    @override_settings(MAMA_CAS_ENABLE_SINGLE_SIGN_OUT=True)
    def test_logout_single_sign_out(self):
        """
        When called with a logged in user and MAMA_CAS_ENABLE_SINGLE_SIGN_OUT
        is set to ``True``, a ``GET`` request to the view should issue
        a POST request for each service accessed by the user.
        """
        ServiceTicketFactory()
        ServiceTicketFactory()
        self.client.login(**self.user_info)
        with patch('requests.post') as mock:
            self.client.get(reverse('cas_logout'))
            self.assertEqual(mock.call_count, 2)


class ValidateViewTests(TestCase):
    url = 'http://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()
        self.rf = RequestFactory()

    def test_validate_view(self):
        """
        When called with no parameters, a validation failure should
        be returned.
        """
        request = self.rf.get(reverse('cas_validate'))
        response = ValidateView.as_view()(request)
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a validation
        failure should be returned.
        """
        request = self.rf.get(reverse('cas_validate'), {'service': 'http://example.org', 'ticket': self.st.ticket})
        response = ValidateView.as_view()(request)
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_invalid_ticket(self):
        """
        When the provided ticket cannot be found, a validation failure
        should be returned.
        """
        st_str = ServiceTicket.objects.create_ticket_str()
        request = self.rf.get(reverse('cas_validate'), {'service': self.url, 'ticket': st_str})
        response = ValidateView.as_view()(request)
        self.assertContains(response, "no\n\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_success(self):
        """
        When called with valid parameters, a validation success should
        be returned. The provided ticket should then be consumed.
        """
        request = self.rf.get(reverse('cas_validate'), {'service': self.url, 'ticket': self.st.ticket})
        response = ValidateView.as_view()(request)
        self.assertContains(response, "yes\nellen\n")
        self.assertEqual(response.get('Content-Type'), 'text/plain')

        st = ServiceTicket.objects.get(ticket=self.st.ticket)
        self.assertTrue(st.is_consumed())


class ServiceValidateViewTests(TestCase):
    url = 'http://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()
        self.rf = RequestFactory()

    def test_service_validate_view(self):
        """
        When called with no parameters, a validation failure should
        be returned.
        """
        request = self.rf.get(reverse('cas_service_validate'))
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_REQUEST')

    def test_service_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a validation
        failure should be returned.
        """
        request = self.rf.get(reverse('cas_service_validate'), {'service': 'http://example.org',
                                                                'ticket': self.st.ticket})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_SERVICE')

    def test_service_validate_view_invalid_ticket(self):
        """
        When the provided ticket cannot be found, a validation failure
        should be returned.
        """
        st_str = ServiceTicket.objects.create_ticket_str()
        request = self.rf.get(reverse('cas_service_validate'), {'service': self.url, 'ticket': st_str})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_TICKET')

    def test_service_validate_view_proxy_ticket(self):
        """
        When a proxy ticket is provided, the validation failure should
        indicate that it was because a proxy ticket was provided.
        """
        pt_str = ProxyTicket.objects.create_ticket_str()
        request = self.rf.get(reverse('cas_service_validate'), {'service': self.url, 'ticket': pt_str})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_TICKET')
        self.assertContains(response, 'Proxy tickets cannot be validated'
                                      ' with /serviceValidate')

    def test_service_validate_view_success(self):
        """
        When called with valid parameters, a validation success should
        be returned. The provided ticket should then be consumed.
        """
        request = self.rf.get(reverse('cas_service_validate'), {'service': self.url, 'ticket': self.st.ticket})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        st = ServiceTicket.objects.get(ticket=self.st.ticket)
        self.assertTrue(st.is_consumed())

    def test_service_validate_view_pgturl(self):
        """
        When called with valid parameters and a ``pgtUrl``, the
        validation success should include a ``ProxyGrantingTicket``.
        """
        request = self.rf.get(reverse('cas_service_validate'), {'service': self.url,
                                                                'ticket': self.st.ticket,
                                                                'pgtUrl': 'https://www.example.com'})
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertContains(response, 'proxyGrantingTicket')

    def test_service_validate_view_pgturl_http(self):
        """
        When called with valid parameters and an invalid ``pgtUrl``,
        the validation success should have no ``ProxyGrantingTicket``.
        """
        request = self.rf.get(reverse('cas_service_validate'), {'service': self.url,
                                                                'ticket': self.st.ticket,
                                                                'pgtUrl': 'http://example.org'})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertNotContains(response, 'proxyGrantingTicket')

    def test_service_validate_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined, a validation
        failure should be returned if the service URL does not match.
        """
        request = self.rf.get(reverse('cas_service_validate'), {'service': 'http://example.org',
                                                                'ticket': self.st.ticket})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_SERVICE')

    @override_settings(MAMA_CAS_ATTRIBUTE_CALLBACKS=('mama_cas.callbacks.user_name_attributes',))
    def test_service_validate_view_attribute_callbacks(self):
        """
        When a custom callback is defined, a validation success should
        include the returned attributes.
        """
        request = self.rf.get(reverse('cas_service_validate'), {'service': self.url, 'ticket': self.st.ticket})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'attributes')
        self.assertContains(response, '<cas:username>ellen</cas:username>')

    def test_service_validate_view_exception_callbacks(self):
        """
        When an attribute callback raises a ValidationError, the exception
        should be handled and cause an authentication failure.
        """
        st = ServiceTicketFactory(service='exception')
        request = self.rf.get(reverse('cas_service_validate'), {'service': 'exception', 'ticket': st.ticket})
        response = ServiceValidateView.as_view()(request)
        self.assertContains(response, 'INTERNAL_ERROR')
        self.assertContains(response, 'Error in attribute callback')


class ProxyValidateViewTests(TestCase):
    url = 'http://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()
        self.pgt = ProxyGrantingTicketFactory()
        self.pt = ProxyTicketFactory()
        self.rf = RequestFactory()

    def test_proxy_validate_view(self):
        """
        When called with no parameters, a validation failure should
        be returned.
        """
        request = self.rf.get(reverse('cas_proxy_validate'))
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_REQUEST')

    def test_proxy_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a validation
        failure should be returned.
        """
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': 'http://example.org',
                                                              'ticket': self.pt.ticket})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_SERVICE')

    def test_proxy_validate_view_invalid_ticket(self):
        """
        When the provided ticket cannot be found, a validation
        failure should be returned.
        """
        pt_str = ProxyTicket.objects.create_ticket_str()
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': self.url, 'ticket': pt_str})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_TICKET')

    def test_proxy_validate_view_st_success(self):
        """
        When called with a valid ``ServiceTicket``, a validation
        success should be returned. The provided ticket should be
        consumed.
        """
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': self.url, 'ticket': self.st.ticket})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        st = ServiceTicket.objects.get(ticket=self.st.ticket)
        self.assertTrue(st.is_consumed())

    def test_proxy_validate_view_pt_success(self):
        """
        When called with a valid ``ProxyTicket``, a validation success
        should be returned. The provided ticket should be consumed.
        """
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': self.url, 'ticket': self.pt.ticket})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        pt = ProxyTicket.objects.get(ticket=self.pt.ticket)
        self.assertTrue(pt.is_consumed())

    def test_proxy_validate_view_proxies(self):
        """
        A validation success should include a ``proxies`` block
        containing all the proxies involved.
        """
        pgt2 = ProxyGrantingTicketFactory(granted_by_pt=self.pt,
                                          granted_by_st=None)
        pt2 = ProxyTicketFactory(service='http://ww2.example.com',
                                 granted_by_pgt=pgt2)
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': pt2.service, 'ticket': pt2.ticket})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertContains(response, 'http://ww2.example.com')
        self.assertContains(response, 'http://www.example.com')

    def test_proxy_validate_view_pgturl(self):
        """
        When called with valid parameters and a ``pgtUrl``, a
        validation success should include a ``ProxyGrantingTicket``.
        """
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': self.url,
                                                              'ticket': self.pt.ticket,
                                                              'pgtUrl': 'https://ww2.example.com'})
        with patch('requests.get') as mock:
            mock.return_value.status_code = 200
            response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertContains(response, 'proxyGrantingTicket')

    def test_proxy_validate_view_pgturl_http(self):
        """
        When called with valid parameters and an invalid ``pgtUrl``,
        the validation success should have no ``ProxyGrantingTicket``.
        """
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': self.url,
                                                              'ticket': self.pt.ticket,
                                                              'pgtUrl': 'https://example.org'})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'authenticationSuccess')
        self.assertNotContains(response, 'proxyGrantingTicket')

    def test_proxy_validate_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined, a validation
        failure should be returned if the service URL does not match.
        """
        request = self.rf.get(reverse('cas_proxy_validate'), {'service': 'http://example.org',
                                                              'ticket': self.pt.ticket})
        response = ProxyValidateView.as_view()(request)
        self.assertContains(response, 'INVALID_SERVICE')


class ProxyViewTests(TestCase):
    url = 'http://www.example.com/'

    def setUp(self):
        self.st = ServiceTicketFactory()
        self.pgt = ProxyGrantingTicketFactory()
        self.rf = RequestFactory()

    def test_proxy_view(self):
        """
        When called with no parameters, a validation failure should be
        returned.
        """
        request = self.rf.get(reverse('cas_proxy'))
        response = ProxyView.as_view()(request)
        self.assertContains(response, 'INVALID_REQUEST')

    def test_proxy_view_no_service(self):
        """
        When called with no service identifier, a validation failure
        should be returned.
        """
        request = self.rf.get(reverse('cas_proxy'), {'pgt': self.pgt.ticket})
        response = ProxyView.as_view()(request)
        self.assertContains(response, 'INVALID_REQUEST')

    def test_proxy_view_invalid_ticket(self):
        """
        When the provided ticket cannot be found, a validation failure
        should be returned.
        """
        pgt_str = ProxyTicket.objects.create_ticket_str()
        request = self.rf.get(reverse('cas_proxy'), {'targetService': self.url, 'pgt': pgt_str})
        response = ProxyView.as_view()(request)
        self.assertContains(response, 'INVALID_TICKET')

    def test_proxy_view_success(self):
        """
        When called with valid parameters, a validation success
        should be returned.
        """
        request = self.rf.get(reverse('cas_proxy'), {'targetService': self.url, 'pgt': self.pgt.ticket})
        response = ProxyView.as_view()(request)
        self.assertContains(response, 'proxyTicket')

    def test_proxy_view_invalid_service_url(self):
        """
        When called with an invalid service identifier, a proxy
        authentication failure should be returned.
        """
        request = self.rf.get(reverse('cas_proxy'), {'targetService': 'http://example.org', 'pgt': self.pgt.ticket})
        response = ProxyView.as_view()(request)
        self.assertContains(response, 'INVALID_SERVICE')


class SamlValidationViewTests(TestCase):
    def setUp(self):
        self.st = ServiceTicketFactory(service='https://www.example.com/')
        self.rf = RequestFactory()

    def test_saml_validation_view(self):
        """
        When called with no parameters, a validation failure should be
        returned.
        """
        request = self.rf.post(reverse('cas_saml_validate'))
        response = SamlValidateView.as_view()(request)
        self.assertContains(response, 'samlp:RequestDenied')

    def test_saml_validation_view_invalid_service(self):
        """
        When called with an invalid service identifier, a validation
        failure should be returned.
        """
        saml = SamlValidateRequest(context={'ticket': self.st})
        request = self.rf.post(build_url('cas_saml_validate', TARGET='https://example.com'),
                               saml.render_content(), content_type='text/xml')
        response = SamlValidateView.as_view()(request)
        self.assertContains(response, 'samlp:RequestDenied')

    def test_saml_validation_view_http_service(self):
        """
        When called with a non-HTTPS service identifier, a validation
        failure should be returned.
        """
        saml = SamlValidateRequest(context={'ticket': self.st})
        request = self.rf.post(build_url('cas_saml_validate', TARGET='http://www.example.com'),
                               saml.render_content(), content_type='text/xml')
        response = SamlValidateView.as_view()(request)
        self.assertContains(response, 'samlp:RequestDenied')

    def test_saml_validation_view_invalid_ticket(self):
        """
        When the provided ticket cannot be found, a validation failure
        should be returned.
        """
        temp_st = ServiceTicketFactory()
        saml = SamlValidateRequest(context={'ticket': temp_st})
        temp_st.delete()
        request = self.rf.post(build_url('cas_saml_validate', TARGET=self.st.service),
                               saml.render_content(), content_type='text/xml')
        response = SamlValidateView.as_view()(request)
        self.assertContains(response, 'samlp:RequestDenied')

    def test_saml_validation_view_success(self):
        """
        When called with valid parameters, a validation success should
        be returned. The provided ticket should then be consumed.
        """
        saml = SamlValidateRequest(context={'ticket': self.st})
        request = self.rf.post(build_url('cas_saml_validate', TARGET=self.st.service),
                               saml.render_content(), content_type='text/xml')
        response = SamlValidateView.as_view()(request)
        self.assertContains(response, 'samlp:Success')

        st = ServiceTicket.objects.get(ticket=self.st.ticket)
        self.assertTrue(st.is_consumed())
