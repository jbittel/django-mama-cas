from django.test import TestCase

from .factories import UserFactory
from mama_cas.callbacks import user_model_attributes
from mama_cas.callbacks import user_name_attributes


class CallbacksTests(TestCase):
    url = 'http://www.example.com/'

    def setUp(self):
        self.user = UserFactory()

    def test_user_name(self):
        """
        The callback should return a username and full_name
        attribute.
        """
        attributes = user_name_attributes(self.user, self.url)
        self.assertIn('username', attributes)
        self.assertEqual(attributes['username'], 'ellen')
        self.assertIn('full_name', attributes)
        self.assertEqual(attributes['full_name'], 'Ellen Cohen')

    def test_user_model_attributes(self):
        """
        The callback should return at least a username attribute.
        """
        attributes = user_model_attributes(self.user, self.url)
        self.assertIn('username', attributes)
        self.assertEqual(attributes['username'], 'ellen')
