import logging

from django.test import TestCase
from django.contrib.auth.models import User

from mama_cas.forms import LoginForm
from mama_cas.forms import LoginFormWarn
from mama_cas.forms import LoginFormEmail


logging.disable(logging.CRITICAL)


class LoginFormTests(TestCase):
    """
    Test the ``LoginForm`` and its subclasses.
    """
    user_info = {'username': 'ellen',
                 'password': 'mamas&papas',
                 'email': 'ellen@example.com'}

    def setUp(self):
        """
        Create a test user for authentication purposes.
        """
        self.user = User.objects.create_user(**self.user_info)

    def test_login_form(self):
        """
        When provided with correct data, the form should validate.
        """
        form = LoginForm(data={'username': 'ellen',
                               'password': 'mamas&papas'})

        self.assertTrue(form.is_valid())

    def test_login_form_invalid(self):
        """
        When provided with incorrect data, the form should not validate.
        """
        form = LoginForm(data={'username': 'denny',
                               'password': 'mamas&papas'})
        self.assertFalse(form.is_valid())

        form = LoginForm(data={'username': 'ellen',
                               'password': 'journeymen'})
        self.assertFalse(form.is_valid())

    def test_login_form_inactive(self):
        """
        When provided with an inactive user, the form should not
        validate.
        """
        self.user.is_active = False
        self.user.save()
        form = LoginForm(data={'username': 'ellen',
                               'password': 'mamas&papas'})
        self.assertFalse(form.is_valid())

    def test_login_form_username(self):
        """
        When a mixed-case username is provided, it should be converted to
        lowercase.
        """
        form = LoginForm(data={'username': 'Ellen',
                               'password': 'mamas&papas'})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'ellen')

    def test_login_form_warn(self):
        """
        The form should contain an additional ``warn`` field.
        """
        form = LoginFormWarn(data={'username': 'ellen',
                                   'password': 'mamas&papas'})

        self.assertTrue(form.is_valid())
        self.assertTrue('warn' in form.fields)

    def test_login_form_email(self):
        """
        If an email address is provided, the username portion should be
        extracted, converted to lowercase and returned as the username.
        """
        form = LoginFormEmail(data={'username': 'Ellen@example.com',
                                    'password': 'mamas&papas'})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'ellen')
