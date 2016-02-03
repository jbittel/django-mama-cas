from django.test import TestCase
from django.test.utils import override_settings

from .factories import InactiveUserFactory
from .factories import UserFactory
from mama_cas.forms import LoginForm
from mama_cas.forms import LoginFormEmail


class LoginFormTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_login_form(self):
        """When provided with correct data, the form should validate."""
        form = LoginForm(data={'username': 'ellen', 'password': 'mamas&papas'})
        self.assertTrue(form.is_valid())

    def test_login_form_empty(self):
        """
        When no username or password is provided, the form should
        be invalid.
        """
        form = LoginForm(data={'username': '', 'password': ''})
        self.assertFalse(form.is_valid())

    def test_login_form_invalid(self):
        """
        When provided with incorrect username or password the form
        should be invalid.
        """
        form = LoginForm(data={'username': 'denny', 'password': 'mamas&papas'})
        self.assertFalse(form.is_valid())

        form = LoginForm(data={'username': 'ellen', 'password': 'journeymen'})
        self.assertFalse(form.is_valid())

    @override_settings(AUTHENTICATION_BACKENDS=('mama_cas.tests.backends.ExceptionBackend',))
    def test_login_form_exception(self):
        """
        If an authentication backend raises an exception, the
        exception should be handled and the form should be invalid.
        """
        form = LoginForm(data={'username': 'ellen', 'password': 'mamas&papas'})
        self.assertFalse(form.is_valid())

    @override_settings(AUTHENTICATION_BACKENDS=('mama_cas.tests.backends.CaseInsensitiveBackend',))
    def test_login_case_insensitive(self):
        """
        If a case-insensitive authentication backend is in use,
        authentication should proceed as expected when the case differs.
        """
        UserFactory(first_name='John', last_name='Phillips')
        form = LoginForm(data={'username': 'John', 'password': 'mamas&papas'})
        self.assertTrue(form.is_valid())

    def test_login_form_inactive(self):
        """
        When provided with an inactive user, the form should be invalid.
        """
        InactiveUserFactory()
        form = LoginForm(data={'username': 'denny', 'password': 'mamas&papas'})
        self.assertFalse(form.is_valid())

    @override_settings(MAMA_CAS_ALLOW_AUTH_WARN=True)
    def test_login_form_warn(self):
        """
        When `MAMA_CAS_ALLOW_AUTH_WARN` is `True` the form should
        contain an additional ``warn`` field.
        """
        form = LoginForm(data={'username': 'ellen', 'password': 'mamas&papas'})
        self.assertTrue('warn' in form.fields)

    def test_login_form_email(self):
        """
        If an email address is provided, the username portion should be
        extracted and returned as the username.
        """
        form = LoginFormEmail(data={'username': 'ellen@example.com', 'password': 'mamas&papas'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'ellen')

    def test_login_form_invalid_username_clean(self):
        """
        If an username is provided such that it becomes invalid when
        cleaned, the form should be invalid.
        """
        form = LoginFormEmail(data={'username': '@example.com', 'password': 'mamas&papas'})
        self.assertFalse(form.is_valid())
