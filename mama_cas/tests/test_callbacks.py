from django.test import TestCase

from .factories import UserFactory
from mama_cas.callbacks import user_model_attributes
from mama_cas.callbacks import user_name_attributes


class CallbacksTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_user_name_attributes(self):
        """
        The callback should return a username, full_name and
        short_name attribute.
        """
        attributes = user_name_attributes(self.user, 'http://www.example.com/')
        self.assertIn('username', attributes)
        self.assertEqual(attributes['username'], 'ellen')
        self.assertIn('full_name', attributes)
        self.assertEqual(attributes['full_name'], 'Ellen Cohen')
        self.assertIn('short_name', attributes)
        self.assertEqual(attributes['short_name'], 'Ellen')

    def test_user_model_attributes(self):
        """The callback should return at least a username attribute."""
        attributes = user_model_attributes(self.user, 'http://www.example.com/')
        self.assertIn('username', attributes)
        self.assertEqual(attributes['username'], 'ellen')
