from django.test import TestCase
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:  # Django version < 1.5
    from django.contrib.auth.models import User

from mama_cas.forms import LoginForm
from mama_cas.forms import LoginFormEmail
from mama_cas.forms import LoginFormWarn


class LoginFormTests(TestCase):
    """
    Test the ``LoginForm`` and its subclasses.
    """
    def setUp(self):
        """
        Initialize the environment for each test.
        """
        self.user = User.objects.create_user(username='ellen',
                                             password='mamas&papas',
                                             email='ellen@example.com')

    def tearDown(self):
        """
        Undo any modifications made to the test environment.
        """
        self.user.delete()

    def test_login_form(self):
        """
        When provided with correct data, the form should validate.
        """
        form = LoginForm(data={'username': 'ellen',
                               'password': 'mamas&papas'})
        self.assertTrue(form.is_valid())

    def test_login_form_invalid(self):
        """
        When provided with incorrect username or password the form
        should not validate.
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

    def test_login_form_warn(self):
        """
        The form should contain an additional ``warn`` field.
        """
        form = LoginFormWarn(data={'username': 'ellen',
                                   'password': 'mamas&papas'})
        self.assertTrue('warn' in form.fields)

    def test_login_form_email(self):
        """
        If an email address is provided, the username portion should be
        extracted and returned as the username.
        """
        form = LoginFormEmail(data={'username': 'ellen@example.com',
                                    'password': 'mamas&papas'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'ellen')
