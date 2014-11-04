.. _settings:

Settings
========

.. currentmodule:: django.conf.settings

None of these settings are required and have sane defaults, but may be used to
customize behavior and improve security. Note that some of these settings
alter stock CAS behavior.

.. attribute:: MAMA_CAS_ALLOW_AUTH_WARN

   :default: ``False``

   If set, allows the user to control transparency of the single sign-on
   process. When enabled, an additional checkbox will be displayed on the
   login form.

.. attribute:: MAMA_CAS_ASYNC_CONCURRENCY

   :default: ``2``

   If single sign-out is enabled and `gevent`_ is installed, this setting
   limits the concurrency of requests sent for a logout event. If the number
   of requests reaches this limit, additional requests block until there is
   room. Setting this value to zero disables this limiting.

.. attribute:: MAMA_CAS_ATTRIBUTE_CALLBACKS

   :default: ``()``

   A tuple of dotted paths to callables that each provide a dictionary of
   name and attribute values. These values are merged together and included
   with a service or proxy validation success. Each callable is provided the
   authenticated ``User`` and the service URL as arguments. For example::

      # In settings.py
      MAMA_CAS_ATTRIBUTE_CALLBACKS = ('path.to.custom_attributes',)

      # In a convenient location
      def custom_attributes(user, service):
          return {'givenName': user.first_name, 'email': user.email}

   Two callbacks are included out of the box for simple use cases and as
   examples for custom callbacks::

      mama_cas.callbacks.user_name_attributes
      mama_cas.callbacks.user_model_attributes

.. attribute:: MAMA_CAS_ENABLE_SINGLE_SIGN_OUT

   :default: ``False``

   If set, causes single sign-out requests to be sent to all accessed services
   when a user logs out. It is up to each service to handle these requests
   and terminate the session appropriately.

   .. note::

      By default, the single sign-out requests are sent synchronously. If
      `gevent`_ is installed, they are sent asynchronously.

.. attribute:: MAMA_CAS_FOLLOW_LOGOUT_URL

   :default: ``True``

   Controls the client redirection behavior at logout when the ``url``
   (CAS 2.0) or ``service`` (CAS 3.0) parameter is provided. When this
   setting is ``True`` and one of these parameters is present, the
   client will be redirected to the specified URL. When this setting
   is ``False``, the client will be redirected to the login page. When
   ``url`` is present, the login page will then display the provided
   URL as a recommended link to follow.

   If neither parameter is specified or is not a valid service URL, the
   client will be redirected to the login page.

.. attribute:: MAMA_CAS_TICKET_EXPIRE

   :default: ``90``

   Controls the length of time, in seconds, between when a service or proxy
   ticket is generated and when it expires. If the ticket is not validated
   before this time has elapsed, it will become invalid. This does **not**
   affect proxy-granting ticket expiration or the duration of a user's single
   sign-on session.

.. attribute:: MAMA_CAS_TICKET_RAND_LEN

   :default: ``32``

   Sets the number of random characters created as part of the ticket string.
   It should be long enough that the ticket string cannot be brute forced
   within a reasonable amount of time. Longer values are more secure, but
   could cause compatibility problems with some clients.

.. attribute:: MAMA_CAS_VALID_SERVICES

   :default: ``()``

   A list of valid Python regular expressions that a service URL is tested
   against when a ticket is validated or the client is redirected. If none of
   the regular expressions match the provided URL, the action fails. If no
   valid services are configured, any service URL is allowed. For example::

      MAMA_CAS_VALID_SERVICES = (
          '^https?://www\.example\.edu/secure',
          '^https://[^\.]+\.example\.com',
      )

   The ``url`` and ``service`` parameters are checked against this list of
   services at logout. If the provided URL does not match one of these regular
   expressions, it is ignored.

.. _gevent: http://www.gevent.org/
