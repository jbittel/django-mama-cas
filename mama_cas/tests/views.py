import logging
import urlparse

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.forms import LoginForm


logging.disable(logging.CRITICAL)


class LoginViewTests(TestCase):
    """
    Test the ``LoginView`` view.
    """
    user_info = { 'username': 'ellen',
                  'password': 'mamas&papas',
                  'email': 'ellen@example.com' }
    service = { 'service': 'http://www.example.com/' }

    def setUp(self):
        """
        Create a test user for authentication purposes.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_login_view(self):
        """
        When called with no parameters, a ``GET`` request to the
        view should display the correct template with a login form.
        """
        response = self.client.get(reverse('cas_login'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mama_cas/login.html')
        self.assertTrue(isinstance(response.context['form'], LoginForm))

    def test_login_view_login(self):
        """
        When called with a valid username and password and no service, a
        ``POST`` request to the view should authenticate and login the user,
        and redirect to the ``LoginView`` view.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)

        self.assertEqual(self.client.session['_auth_user_id'], self.user.pk)
        self.assertRedirects(response, reverse('cas_login'))

    def test_login_view_login_service(self):
        """
        When called with a valid username, password and service, a ``POST``
        request to the view should authenticate and login the user, create a
        ``ServiceTicket`` and redirect to the supplied service URL with a
        ticket parameter.
        """
        self.user_info.update(self.service)
        response = self.client.post(reverse('cas_login'), self.user_info)

        self.assertEqual(self.client.session['_auth_user_id'], self.user.pk)
        self.assertEqual(ServiceTicket.objects.count(), 1)
        # Check that the client is redirected properly without actually
        # trying to load the destination page
        parts = list(urlparse.urlparse(response['Location']))
        query = dict(urlparse.parse_qsl(parts[4]))
        destination = "%s://%s%s" % (parts[0], parts[1], parts[2])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(destination, self.user_info['service'])
        self.assertTrue('ticket' in query)

class LogoutViewTests(TestCase):
    """
    Test the ``LogoutView`` view.
    """
    user_info = { 'username': 'ellen',
                  'password': 'mamas&papas',
                  'email': 'ellen@example.com' }

    def setUp(self):
        """
        Create a test user for authentication purposes.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_logout_view(self):
        """
        When called with no parameters and no logged in user, a ``GET``
        request to the view should simply display the correct template.
        """
        response = self.client.get(reverse('cas_logout'))

        self.assertEqual(response.status_code, 302)

    def test_logout_view_post(self):
        """
        A ``POST`` request to the view should return an error that the method
        is not allowed.
        """
        response = self.client.post(reverse('cas_logout'))

        self.assertEqual(response.status_code, 405)

    def test_logout_view_success(self):
        """
        When called with a logged in user, a ``GET`` request to the
        view should log the user out and display the correct template.
        """
        response = self.client.post(reverse('cas_login'), self.user_info)
        response = self.client.get(reverse('cas_logout'))

        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertEqual(response.status_code, 302)

class ValidateViewTests(TestCase):
    """
    Test the ``ValidateView`` view.
    """
    invalid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = { 'username': 'ellen',
                  'password': 'mamas&papas',
                  'email': 'ellen@example.com' }
    ticket_info = { 'service': valid_service }
    validation_failure = "no\n\n"
    validation_success = "yes\n%s\n" % user_info['username']

    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({ 'user': self.user })
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)

    def test_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_validate'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.validation_failure)
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_post(self):
        """
        A ``POST`` request to the view should return an error that the method
        is not allowed.
        """
        response = self.client.post(reverse('cas_validate'))

        self.assertEqual(response.status_code, 405)

    def test_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a ``GET`` request to
        the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service, self.st.ticket)
        response = self.client.get(reverse('cas_validate') + query_str)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.validation_failure)
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET`` request
        to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.invalid_st_str)
        response = self.client.get(reverse('cas_validate') + query_str)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.validation_failure)
        self.assertEqual(response.get('Content-Type'), 'text/plain')

    def test_validate_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the view
        should return a validation success and the service ticket should be
        consumed and invalid for future validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.st.ticket)
        response = self.client.get(reverse('cas_validate') + query_str)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.validation_success)
        self.assertEqual(response.get('Content-Type'), 'text/plain')

        response = self.client.get(reverse('cas_validate') + query_str)
        # This should be a validation failure as the ticket was consumed in
        # the preceeding validation request
        self.assertEqual(response.content, self.validation_failure)
        self.assertEqual(response.get('Content-Type'), 'text/plain')

class ServiceValidateViewTests(TestCase):
    """
    Test the ``ServiceValidateView`` view.
    """
    invalid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = { 'username': 'ellen',
                  'password': 'mamas&papas',
                  'email': 'ellen@example.com' }
    ticket_info = { 'service': valid_service }
    valid_pgt_url = 'https://www.example.com/'
    invalid_pgt_url = 'http://www.example.com/'

    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({'user': self.user})
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)

    def test_service_validate_view_get(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_service_validate'))

        self.assertContains(response, 'INVALID_REQUEST', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_post(self):
        """
        A ``POST`` request to the view should return an error that the method
        is not allowed.
        """
        response = self.client.post(reverse('cas_service_validate'))

        self.assertEqual(response.status_code, 405)

    def test_service_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a ``GET`` request
        to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service, self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)

        self.assertContains(response, 'INVALID_SERVICE', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET`` request
        to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.invalid_st_str)
        response = self.client.get(reverse('cas_service_validate') + query_str)

        self.assertContains(response, 'INVALID_TICKET', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the view
        should return a validation success and the service ticket should be
        consumed and invalid for future validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)

        self.assertContains(response, 'authenticationSuccess', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        response = self.client.get(reverse('cas_service_validate') + query_str)
        # This test should fail as the ticket was consumed in the preceeding test
        self.assertContains(response, 'INVALID_TICKET', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter, a
        ``GET`` request to the view should return a validation success and
        also attempt to create a ``ProxyGrantingTicket``.

        This test will fail unless ``valid_pgt_url`` is configured with a
        valid responding proxy callback URL.
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.valid_service,
                                                         self.st.ticket,
                                                         self.valid_pgt_url)
        response = self.client.get(reverse('cas_service_validate') + query_str)

        self.assertContains(response, 'authenticationSuccess', status_code=200)
        self.assertContains(response, 'proxyGrantingTicket', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_pgturl_http(self):
        """
        When called with correct parameters and an invalid HTTP ``pgtUrl``
        parameter, a ``GET`` request to the view should return a validation
        success with no ``ProxyGrantingTicket`` (``pgtUrl`` must be HTTPS).
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.valid_service,
                                                         self.st.ticket,
                                                         self.invalid_pgt_url)
        response = self.client.get(reverse('cas_service_validate') + query_str)

        self.assertContains(response, 'authenticationSuccess', status_code=200)
        self.assertNotContains(response, 'proxyGrantingTicket', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

class ProxyViewTests(TestCase):
    """
    Test the ``ProxyView`` view.
    """
    invalid_pgt_str = 'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_service = 'http://www.example.com/'
    user_info = { 'username': 'ellen',
                  'password': 'mamas&papas',
                  'email': 'ellen@example.com' }
    ticket_info = { 'service': valid_service }

    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({'user': self.user})
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                             validate=False,
                                                             user=self.user,
                                                             granted_by_st=self.st)

    def test_proxy_view_get(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_proxy'))

        self.assertContains(response, 'INVALID_REQUEST', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_view_post(self):
        """
        A ``POST`` request to the view should return an error that the method
        is not allowed.
        """
        response = self.client.post(reverse('cas_proxy'))

        self.assertEqual(response.status_code, 405)

    def test_proxy_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET`` request to
        the view should return a validation failure.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.valid_service,
                                                  self.invalid_pgt_str)
        response = self.client.get(reverse('cas_proxy') + query_str)

        self.assertContains(response, 'BAD_PGT', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the view
        should return a validation success with an included ``ProxyTicket``.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.valid_service,
                                                  self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)

        self.assertContains(response, 'proxyTicket', status_code=200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
