import logging

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from mama_cas.models import ServiceTicket
from mama_cas.models import TicketGrantingTicket
from mama_cas.forms import LoginForm


logging.disable(logging.CRITICAL)


class LoginViewTests(TestCase):
    def setUp(self):
        """
        Create a test user for authentication purposes.

        """
        self.user = User.objects.create_user('test', 'test@localhost.com', 'testing')

    def test_login_view(self):
        """
        When called with no parameters, a ``GET`` request to the ``login``
        view should display the correct template with a login form.

        """
        response = self.client.get(reverse('cas_login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mama_cas/login.html')
        self.assertTrue(isinstance(response.context['form'], LoginForm))

    def test_login_view_login(self):
        """
        When called with a valid username and password, a ``POST`` request to
        the ``login`` view should create a new ``TicketGrantingTicket`` with a
        corresponding ticket-granting cookie and redirect to the ``login``
        view.

        """
        response = self.client.post(reverse('cas_login'),
                                    data={'username': 'test',
                                          'password': 'testing'})
        self.assertRedirects(response, reverse('cas_login'))
        self.assertTrue('tgc' in self.client.cookies)
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)

    def test_login_view_login_service(self):
        """
        When called with a valid username, password and service, a ``POST``
        request to the ``login`` view should create a new
        ``TicketGrantingTicket`` with a corresponding ticket-granting cookie
        and redirect to the ``login`` view with the service included as a
        query parameter.

        """
        response = self.client.post(reverse('cas_login'),
                                    data={'username': 'test',
                                          'password': 'testing',
                                          'service': 'http://test.localhost.com/'})
        query_str = '?service=http://test.localhost.com/'
        self.assertRedirects(response, reverse('cas_login') + query_str)
        self.assertTrue('tgc' in self.client.cookies)
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)

class LogoutViewTests(TestCase):
    def setUp(self):
        """
        Create a test user for authentication purposes.

        """
        self.user = User.objects.create_user('test', 'test@localhost.com', 'testing')

    def test_logout_view(self):
        """
        When called with no parameters and no cookie, a ``GET`` request
        to the ``logout`` view should display the correct template.

        """
        response = self.client.get(reverse('cas_logout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mama_cas/logout.html')

    def test_logout_view_success(self):
        """
        When called with a valid ticket granting cookie set, a ``GET``
        request to the ``logout`` view should invalidate the cookie,
        consume the ticket and display the correct template.

        """
        response = self.client.post(reverse('cas_login'),
                                    data={'username': 'test',
                                          'password': 'testing'})
        self.assertRedirects(response, reverse('cas_login'))
        self.assertTrue('tgc' in self.client.cookies)
        self.assertEqual(TicketGrantingTicket.objects.count(), 1)

        response = self.client.get(reverse('cas_logout'))
        self.assertEqual(self.client.cookies['tgc']['expires'], 'Thu, 01-Jan-1970 00:00:00 GMT')
        TicketGrantingTicket.objects.delete_invalid_tickets()
        self.assertEqual(TicketGrantingTicket.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mama_cas/logout.html')

class ValidateViewTests(TestCase):
    valid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ticket_info = {'service': 'http://www.test.com/'}

    def setUp(self):
        """
        Create a valid ticket-granting ticket and service ticket for
        testing purposes.

        """
        self.tgt = TicketGrantingTicket.objects.create_ticket(username='test', client_ip='127.0.0.1')
        self.ticket_info.update({'granted_by_tgt': self.tgt})
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)

    def test_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the validate
        view should return 'no\n\n'.

        """
        response = self.client.get(reverse('cas_validate'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "no\n\n")

    def test_validate_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the
        validate view should return 'yes\n<username>\n'.

        """
        query_str = "?service=%s&ticket=%s" % (self.ticket_info['service'], self.st.ticket)
        response = self.client.get(reverse('cas_validate') + query_str)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "yes\ntest\n")
