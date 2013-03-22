.. _settings:

Settings
========

.. currentmodule:: django.conf.settings

django-mama-cas can be configured using several custom settings. None are
required and have sane defaults, but can be used to customize the behavior.

.. attribute:: MAMA_CAS_TICKET_EXPIRE

   :default: ``5``

   Controls the length of time, in minutes, between when a service or proxy
   ticket is generated and when it expires. If the ticket is not validated
   before this time has elapsed, it will become invalid. This does **not**
   affect the duration of a user's single sign-on session.

.. attribute:: MAMA_CAS_TICKET_RAND_LEN

   :default: ``32``

   Sets the number of random characters created as part of the ticket string.
   It should be long enough that the ticket string cannot be brute forced
   within a reasonable amount of time. Longer values are more secure, but
   could cause compatibility problems with some clients.

.. attribute:: MAMA_CAS_USER_ATTRIBUTES

   :default: ``{}``

   A dictionary of name and User attribute values to be returned along with a
   service or proxy validation success. The key can be any meaningful string,
   while the value must correspond with an attribute on the User object. For
   example::

      MAMA_CAS_USER_ATTRIBUTES = {
          'givenName': 'first_name',
          'sn': 'last_name',
          'email': 'email',
      }

.. attribute:: MAMA_CAS_PROFILE_ATTRIBUTES

   :default: ``{}``

   A dictionary of name and User profile attribute values to be returned along
   with a service or proxy validation success. The key can be any meaningful
   string, while the value must correspond with an attribute on the User
   profile object. If no User profile is configured or available, this setting
   will be ignored. For example::

      MAMA_CAS_PROFILE_ATTRIBUTES = {
          'employeeID': 'id_number',
      }

   .. note::

      This setting is intended for use with Django 1.4. In Django 1.5 and later,
      the recommended method for storing custom profile information is through a
      `custom User model`_.

.. _custom user model: https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#auth-custom-user


.. attribute:: MAMA_CAS_VALID_SERVICES

   :default: ``()``

   A list of valid Python regular expressions that a service URL is tested
   against when a ticket is validated. If none of the regular expressions
   match the provided URL, the request fails. If no valid services are
   configured, any service URL is allowed. For example::

      MAMA_CAS_VALID_SERVICES = (
          'https?://www\.example\.edu/secure/.*',
          'https://.*\.example\.com/.*',
      )

   The logout ``url`` parameter is also checked against this list of services.
   If the provided URL does not match one of these regular expressions, it
   will not be displayed to the user.
