import logging
import random
import string
import urlparse
import urllib
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import fromstring

from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from mama_cas.models import ServiceTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ProxyGrantingTicket
from mama_cas.forms import LoginForm
from mama_cas.forms import LoginFormWarn


logging.disable(logging.CRITICAL)

XMLNS = '{http://www.yale.edu/tp/cas}'


class LoginViewTests(TestCase):
    """
    Test the ``LoginView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    service = {'service': 'http://www.example.com/'}

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
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

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


class WarnViewTests(TestCase):
    """
    Test the ``WarnView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    valid_service = 'http://www.example.com/'
    form_data = user_info.copy()
    form_data.update({'warn': 'true'})

    def setUp(self):
        """
        Create a test user for authentication purposes.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_warn_view(self):
        """
        When called with no parameters and no logged in user, a ``GET``
        request to the view should simply redirect to the login view.
        """
        response = self.client.get(reverse('cas_warn'))

        self.assertRedirects(response, reverse('cas_login'), status_code=302,
                             target_status_code=200)
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_warn_view_redirect(self):
        """
        When a user logs in with the warn parameter present, the user's
        session should contain a ``warn`` attribute and a ``ServiceTicket``
        request to the credential requestor should redirect to the warn view.
        """
        # Only continue the test if the required form class is in use
        response = self.client.get(reverse('cas_login'))
        if isinstance(response.context['form'], LoginFormWarn):
            response = self.client.post(reverse('cas_login'), self.form_data)
            query_str = "?service=%s" % urllib.quote(self.valid_service, '')
            response = self.client.get(reverse('cas_login') + query_str)

            self.assertEqual(self.client.session.get('warn'), True)
            self.assertRedirects(response, reverse('cas_warn') + query_str,
                                 status_code=302, target_status_code=200)

    def test_warn_view_display(self):
        """
        When called with a logged in user, a request to the warn view should
        display the correct template containing the provided service string.
        """
        self.client.login(username=self.user_info['username'],
                          password=self.user_info['password'])
        query_str = "?service=%s" % urllib.quote(self.valid_service, '')
        response = self.client.get(reverse('cas_warn') + query_str)

        self.assertContains(response, self.valid_service, status_code=200)
        self.assertTemplateUsed(response, 'mama_cas/warn.html')

    def test_warn_view_warned(self):
        """
        When a logged in user submits the form on the warn view, the user
        should be redirected to the login view with the ``warned`` parameter
        present.
        """
        self.client.login(username=self.user_info['username'],
                          password=self.user_info['password'])
        response = self.client.post(reverse('cas_warn'))

        self.assertRedirects(response, reverse('cas_login') + '?warned=true',
                             status_code=302, target_status_code=200)


class LogoutViewTests(TestCase):
    """
    Test the ``LogoutView`` view.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}

    def setUp(self):
        """
        Create a test user for authentication purposes.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_logout_view(self):
        """
        When called with no parameters and no logged in user, a ``GET``
        request to the view should simply redirect to the login view.
        """
        response = self.client.get(reverse('cas_logout'))

        self.assertRedirects(response, reverse('cas_login'),
                             status_code=302, target_status_code=200)
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

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

        self.assertRedirects(response, reverse('cas_login'),
                             status_code=302, target_status_code=200)
        self.assertFalse('_auth_user_id' in self.client.session)


class ValidateViewTests(TestCase):
    """
    Test the ``ValidateView`` view.
    """
    invalid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    ticket_info = {'service': valid_service}
    validation_failure = "no\n\n"
    validation_success = "yes\n%s\n" % user_info['username']

    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.ticket_info.update({'user': self.user})
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)

        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_validate'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.validation_failure)
        self.assertEqual(response.get('Content-Type'), 'text/plain')
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

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
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    user_attr = {'givenName': 'first_name',
                 'sn': 'last_name',
                 'email': 'email'}
    ticket_info = {'service': valid_service}
    valid_pgt_url = 'https://www.example.com/'
    invalid_pgt_url = 'http://www.example.com/'
    invalid_attr = {'invalid':
            ''.join(random.choice(string.ascii_letters) for x in range(10))}

    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.user.first_name = 'Ellen'
        self.user.last_name = 'Cohen'
        self.user.save()

        self.ticket_info.update({'user': self.user})
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)

        self.old_user_attributes = getattr(settings, 'MAMA_CAS_USER_ATTRIBUTES', {})
        if not self.old_user_attributes:
            settings.MAMA_CAS_USER_ATTRIBUTES = self.user_attr
        settings.MAMA_CAS_USER_ATTRIBUTES.update(self.invalid_attr)
        self.old_profile_attributes = getattr(settings, 'MAMA_CAS_PROFILE_ATTRIBUTES', {})
        if not self.old_profile_attributes:
            settings.MAMA_CAS_PROFILE_ATTRIBUTES = {}
        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_USER_ATTRIBUTES = self.old_user_attributes
        settings.MAMA_CAS_PROFILE_ATTRIBUTES = self.old_profile_attributes
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_service_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_service_validate'))
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_REQUEST')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

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
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_SERVICE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET`` request
        to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.invalid_st_str)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_TICKET')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the view
        should return a validation success and the ``ServiceTicket`` should be
        consumed and invalid for future validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        # This request should fail as the ticket was consumed in the preceeding test
        response = self.client.get(reverse('cas_service_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_TICKET')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_service_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter, a
        ``GET`` request to the view should return a validation success and
        also attempt to create a ``ProxyGrantingTicket``.

        NOTE: this test will fail unless ``valid_pgt_url`` is configured with
        a valid proxy callback URL.
        """
        if self.valid_pgt_url == 'https://www.example.com/':
            raise ImproperlyConfigured("Set valid_pgt_url to a valid HTTPS "
                                       "URL to successfully run this test")

        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.valid_service,
                                                         self.st.ticket,
                                                         self.valid_pgt_url)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'proxyGrantingTicket')
        self.assertIsNotNone(elem)

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
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'proxyGrantingTicket')
        self.assertIsNone(elem)

    def test_service_validate_view_user_attributes(self):
        """
        When ``MAMA_CAS_USER_ATTRIBUTES`` is defined in the settings file, a
        service validation success should include the list of configured user
        attributes.
        """
        attr_names = settings.MAMA_CAS_USER_ATTRIBUTES.keys()
        attr_names.extend(settings.MAMA_CAS_PROFILE_ATTRIBUTES.keys())
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'attributes')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
        self.assertIsNotNone(elem)
        # Because attribute order is not guaranteed, we take a list of all
        # configured attributes, compare each attribute found to make sure
        # it's present and then remove it from the temporary list.
        #
        # When done, check that the temporary list is empty to verify that
        # all configured attributes were matched.
        for attribute in elem:
            attribute.tag = attribute.tag[len(XMLNS):]
            self.assertTrue(attribute.tag in attr_names)
            attr_names.remove(attribute.tag)
        self.assertEqual(len(attr_names), 0)

    def test_service_validate_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined in the settings file, a
        service string should be checked against the list of valid services.
        If it does not match, a service authentication failure should be
        returned.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service,
                                               self.st.ticket)
        response = self.client.get(reverse('cas_service_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_SERVICE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')


class ProxyValidateViewTests(TestCase):
    """
    Test the ``ProxyValidateView`` view.
    """
    invalid_st_str = 'ST-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    invalid_pt_str = 'PT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_service = 'http://www.example.com/'
    valid_service2 = 'http://ww2.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    user_attr = {'givenName': 'first_name',
                 'sn': 'last_name',
                 'email': 'email'}
    ticket_info = {'service': valid_service}
    valid_pgt_url = 'https://www.example.com/'
    invalid_pgt_url = 'http://www.example.com/'
    invalid_attr = {'invalid':
            ''.join(random.choice(string.ascii_letters) for x in range(10))}


    def setUp(self):
        """
        Create a valid user and service ticket for testing purposes.
        """
        self.user = User.objects.create_user(**self.user_info)
        self.user.first_name = 'Ellen'
        self.user.last_name = 'Cohen'
        self.user.save()

        self.ticket_info.update({'user': self.user})
        self.st = ServiceTicket.objects.create_ticket(**self.ticket_info)
        self.pgt = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                             validate=False,
                                                             user=self.user,
                                                             granted_by_st=self.st)
        self.pt = ProxyTicket.objects.create_ticket(granted_by_pgt=self.pgt,
                                                    **self.ticket_info)

        self.old_user_attributes = getattr(settings, 'MAMA_CAS_USER_ATTRIBUTES', {})
        if not self.old_user_attributes:
            settings.MAMA_CAS_USER_ATTRIBUTES = self.user_attr
        settings.MAMA_CAS_USER_ATTRIBUTES.update(self.invalid_attr)
        self.old_profile_attributes = getattr(settings, 'MAMA_CAS_PROFILE_ATTRIBUTES', {})
        if not self.old_profile_attributes:
            settings.MAMA_CAS_PROFILE_ATTRIBUTES = {}
        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,
                                            self.valid_service2)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_USER_ATTRIBUTES = self.old_user_attributes
        settings.MAMA_CAS_PROFILE_ATTRIBUTES = self.old_profile_attributes
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_proxy_validate_view(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_proxy_validate'))
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_REQUEST')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_proxy_validate_view_post(self):
        """
        A ``POST`` request to the view should return an error that the method
        is not allowed.
        """
        response = self.client.post(reverse('cas_proxy_validate'))

        self.assertEqual(response.status_code, 405)

    def test_proxy_validate_view_invalid_service(self):
        """
        When called with an invalid service identifier, a ``GET`` request
        to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service, self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_SERVICE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_validate_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET`` request
        to the view should return a validation failure.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.invalid_pt_str)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_TICKET')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_validate_view_st_success(self):
        """
        When called with a valid ``ServiceTicket``, a ``GET`` request to the
        view should return a validation success and the ``ServiceTicket``
        should be consumed and invalid for future validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.st.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        # This request should fail as the ticket was consumed in the preceeding test
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_TICKET')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_validate_view_pt_success(self):
        """
        When called with a valid ``ProxyTicket``, a ``GET`` request to the
        view should return a validation success and the ``ProxyTicket`` should
        be consumed and invalid for future validation attempts.
        """
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'proxies')
        proxy = list(elem.getiterator(XMLNS + 'proxy'))
        self.assertEqual(len(proxy), 1)
        self.assertEqual(proxy[0].text, 'http://www.example.com')

        # This request should fail as the ticket was consumed in the preceeding test
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_TICKET')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_validate_view_proxies(self):
        """
        When a successful ``ProxyTicket`` validation occurs, the response
        should include a ``proxies`` block containing all of the proxies
        involved. When authentication has proceeded through multiple proxies,
        they must be listed in reverse order of being accessed.
        """
        pgt2 = ProxyGrantingTicket.objects.create_ticket(self.valid_service,
                                                         validate=False,
                                                         user=self.user,
                                                         granted_by_pt=self.pt)
        ticket_info2 = {'service': self.valid_service2,
                        'user': self.user}
        pt2 = ProxyTicket.objects.create_ticket(granted_by_pgt=pgt2,
                                                **ticket_info2)
        query_str = "?service=%s&ticket=%s" % (self.valid_service2, pt2)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'proxies')
        proxy = list(elem.getiterator(XMLNS + 'proxy'))
        self.assertEqual(len(proxy), 2)
        self.assertEqual(proxy[0].text, 'http://ww2.example.com')
        self.assertEqual(proxy[1].text, 'http://www.example.com')

    def test_proxy_validate_view_pgturl(self):
        """
        When called with correct parameters and a ``pgtUrl`` parameter, a
        ``GET`` request to the view should return a validation success and
        also attempt to create a ``ProxyGrantingTicket``.

        NOTE: this test will fail unless ``valid_pgt_url`` is configured with
        a valid proxy callback URL.
        """
        if self.valid_pgt_url == 'https://www.example.com/':
            raise ImproperlyConfigured("Set valid_pgt_url to a valid HTTPS "
                                       "URL to successfully run this test")

        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.valid_service,
                                                         self.pt.ticket,
                                                         self.valid_pgt_url)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'proxyGrantingTicket')
        self.assertIsNotNone(elem)

    def test_proxy_validate_view_pgturl_http(self):
        """
        When called with correct parameters and an invalid HTTP ``pgtUrl``
        parameter, a ``GET`` request to the view should return a validation
        success with no ``ProxyGrantingTicket`` (``pgtUrl`` must be HTTPS).
        """
        query_str = "?service=%s&ticket=%s&pgtUrl=%s" % (self.valid_service,
                                                         self.pt.ticket,
                                                         self.invalid_pgt_url)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'user')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, self.user_info['username'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'proxyGrantingTicket')
        self.assertIsNone(elem)

    def test_proxy_validate_view_user_attributes(self):
        """
        When ``MAMA_CAS_USER_ATTRIBUTES`` is defined in the settings file, a
        proxy validation success should include the list of configured user
        attributes.
        """
        attr_names = settings.MAMA_CAS_USER_ATTRIBUTES.keys()
        attr_names.extend(settings.MAMA_CAS_PROFILE_ATTRIBUTES.keys())
        query_str = "?service=%s&ticket=%s" % (self.valid_service, self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationSuccess/' + XMLNS + 'attributes')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
        self.assertIsNotNone(elem)
        # Because attribute order is not guaranteed, we take a list of all
        # configured attributes, compare each attribute found to make sure
        # it's present and then remove it from the temporary list.
        #
        # When done, check that the temporary list is empty to verify that
        # all configured attributes were matched.
        for attribute in elem:
            attribute.tag = attribute.tag[len(XMLNS):]
            self.assertTrue(attribute.tag in attr_names)
            attr_names.remove(attribute.tag)
        self.assertEqual(len(attr_names), 0)

    def test_proxy_validate_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined in the settings file, a
        service string should be checked against the list of valid services.
        If it does not match, a proxy authentication failure should be
        returned.
        """
        query_str = "?service=%s&ticket=%s" % (self.invalid_service,
                                               self.pt.ticket)
        response = self.client.get(reverse('cas_proxy_validate') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'authenticationFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_SERVICE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')


class ProxyViewTests(TestCase):
    """
    Test the ``ProxyView`` view.
    """
    invalid_pgt_str = 'PGT-0000000000-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    valid_service = 'http://www.example.com/'
    invalid_service = 'http://www.example.org/'
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}
    ticket_info = {'service': valid_service}

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

        self.old_valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
        settings.MAMA_CAS_VALID_SERVICES = (self.valid_service,)

    def tearDown(self):
        """
        Undo any modifications made to settings.
        """
        settings.MAMA_CAS_VALID_SERVICES = self.old_valid_services

    def test_proxy_view(self):
        """
        When called with no parameters, a ``GET`` request to the view should
        return a validation failure.
        """
        response = self.client.get(reverse('cas_proxy'))
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'proxyFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_REQUEST')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
        self.assertTrue('Cache-Control' in response)
        self.assertEqual(response['Cache-Control'], 'max-age=0')

    def test_proxy_view_post(self):
        """
        A ``POST`` request to the view should return an error that the method
        is not allowed.
        """
        response = self.client.post(reverse('cas_proxy'))

        self.assertEqual(response.status_code, 405)

    def test_proxy_view_no_service(self):
        """
        When called with no service identifier, a ``GET`` request to the view
        should return a validation failure.
        """
        query_str = "?pgt=%s" % (self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'proxyFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_REQUEST')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_view_invalid_ticket(self):
        """
        When called with an invalid ticket identifier, a ``GET`` request to
        the view should return a validation failure.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.valid_service,
                                                  self.invalid_pgt_str)
        response = self.client.get(reverse('cas_proxy') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'proxyFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'BAD_PGT')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_view_success(self):
        """
        When called with correct parameters, a ``GET`` request to the view
        should return a validation success with an included ``ProxyTicket``.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.valid_service,
                                                  self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'proxySuccess/' + XMLNS + 'proxyTicket')

        self.assertIsNotNone(elem)
        self.assertNotEqual(elem.text, 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')

    def test_proxy_view_invalid_service_url(self):
        """
        When ``MAMA_CAS_VALID_SERVICES`` is defined in the settings file, a
        service string should be checked against the list of valid services.
        If it does not match, a proxy authentication failure should be
        returned.
        """
        query_str = "?targetService=%s&pgt=%s" % (self.invalid_service,
                                                  self.pgt.ticket)
        response = self.client.get(reverse('cas_proxy') + query_str)
        tree = ElementTree(fromstring(response.content))
        elem = tree.find(XMLNS + 'proxyFailure')

        self.assertIsNotNone(elem)
        self.assertEqual(elem.get('code'), 'INVALID_SERVICE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'text/xml')
