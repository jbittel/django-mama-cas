.. _getting-started:

Getting started
===============

Prerequisites
-------------

The primary prerequesite of django-mama-cas is `Django
<http://www.djangoproject.com>`_ itself. For django-mama-cas |version|, Django
1.4 or later is required. Earlier versions of Django may work, but are not
tested or supported. See the `Django downloads
<https://www.djangoproject.com/download/>`_ page for information on
downloading and installing Django.

The Python `requests <http://python-requests.org/>`_ library is also required,
but should be automatically installed during the installation process
described below.

You will also need at least one `authentication backend
<http://pypi.python.org/pypi?:action=browse&c=475&c=523>`_
`installed and configured
<https://docs.djangoproject.com/en/dev/topics/auth/#specifying-authentication-backends>`_,
depending on your authoritative authentication source.

Installing django-mama-cas
--------------------------

Via pip
~~~~~~~

The easiest way to install django-mama-cas is using pip. Simply type::

   pip install django-mama-cas

It is recommended to run this command within a
`virtualenv <http://www.virtualenv.org>`_ so django-mama-cas is installed
in an isolated environment instead of system wide.

Via a downloaded package
~~~~~~~~~~~~~~~~~~~~~~~~

You can also manually download django-mama-cas from
`GitHub <https://github.com/jbittel/django-mama-cas>`_. Extract the downloaded
archive and install it with::

   python setup.py install

Alternately, you can manually put django-mama-cas anywhere, provided it is on
the Python path. If you take the route, you will also need to manually install
the `requests library <http://python-requests.org>`_ dependency.

Configuration
-------------

Once installed, add django-mama-cas to your project by modifying the
``INSTALLED_APPS`` setting within your project's ``settings.py`` to include
this line::

   'mama_cas',

Once django-mama-cas is added to the project, run ``python manage.py syncdb``
to create the required database tables.

Settings
~~~~~~~~

django-mama-cas can be modified using several custom settings. None are
required, but can be used to override the defaults.

**MAMA_CAS_TICKET_EXPIRE (default: 5)**
   Controls the length of time, in minutes, between when a service or proxy
   ticket is generated and when it expires. If the ticket is not validated
   before this time is up, it will become invalid. This does NOT affect the
   duration of a user's single sign-on session.

**MAMA_CAS_TICKET_RAND_LEN (default: 32)**
   Sets the number of random characters created as part of the ticket string.
   It should be long enough that the ticket cannot be brute forced within a
   reasonable amount of time. Longer values are more secure, but could cause
   compatibility problems with some clients.

**MAMA_CAS_USER_ATTRIBUTES (default: {})**
   A dictionary of name and ``User`` attribute values to be returned along
   with a service or proxy validation success. The key can be any meaningful
   string, while the value must correspond with an attribute on the
   ``User`` object. For example::

      MAMA_CAS_USER_ATTRIBUTES = {
          'givenName': 'first_name',
          'sn': 'last_name',
          'email': 'email',
      }

**MAMA_CAS_PROFILE_ATTRIBUTES (default: {})**
   A dictionary of name and user profile attribute values to be returned along
   with a service or proxy validation success. The key can be any meaningful
   string, while the value must correspond with an attribute on the user
   profile object. If no user profile is configured or available, this setting
   will be ignored. For example::

      MAMA_CAS_PROFILE_ATTRIBUTES = {
          'employeeID': 'id_number',
      }

**MAMA_CAS_VALID_SERVICES (default: ())**
   A list of valid service regular expressions that a service URL is tested
   against when a ticket is validated. If none of the regular expressions
   match the provided URL, the request fails. Any valid Python regular
   expression is accepted. If no valid services are configured, any service
   URL will be allowed. For example::

      MAMA_CAS_VALID_SERVICES = (
          'https?://www\.example\.edu/secure/.*',
          'https://.*\.example\.com/.*',
      )

Sessions
~~~~~~~~

django-mama-cas relies on standard Django sessions to control session storage
and expiration. To understand how sessions work within Django, read the
`session documentation <https://docs.djangoproject.com/en/dev/topics/http/sessions/>`_.
There are three particular settings that control where sessions are stored and
when they expire:

   * `SESSION_ENGINE
     <https://docs.djangoproject.com/en/dev/topics/http/sessions/#session-engine>`_
   * `SESSION_COOKIE_AGE
     <https://docs.djangoproject.com/en/dev/topics/http/sessions/#session-cookie-age>`_
   * `SESSION_EXPIRE_AT_BROWSER_CLOSE
     <https://docs.djangoproject.com/en/dev/topics/http/sessions/#session-expire-at-browser-close>`_

It is recommended that ``SESSION_COOKIE_AGE`` be set shorter than the default
of two weeks. ``SESSION_EXPIRE_AT_BROWSER_CLOSE`` should be set to ``True``
to conform to the CAS specification. Both of these settings can be configured
to meet your particular environment and security needs.

URL paths
~~~~~~~~~

django-mama-cas includes a Django ``URLconf`` that provides the required CAS
URIs (e.g. login, logout, validate, etc.). They are located in
``mama_cas.urls`` and can be included directly in your project's root
``URLconf``. For example::

   (r'', include('mama_cas.urls')),

This would make the CAS server available at the top level of your project's
URLs. If this is not the desired path, add a base to the included URLs. For
example, if you wished the CAS server to be available under the ``/cas/``
root, use::

   (r'^cas/', include('mama_cas.urls')),

All CAS enabled services need to be configured according to the URL settings
here. Changing the CAS URLs within ``mama_cas.urls`` is not recommended as
that will likely break standard CAS behavior.

Templates
~~~~~~~~~

django-mama-cas comes with a basic login template implementing standard
username and password authentication. It will work as provided, but can also
be extended or replaced according to your needs.

If you are returning custom user attributes with a service or proxy validation
response, you may also need to change the validation XML template to return
the attributes in the correct format.

Read the :ref:`template documentation <templates>` for more information on the
included templates and customization.

Authentication
--------------

django-mama-cas does not perform any authentication itself. It relies on the
configured Django authentication backends for that task. The process of
configuring authentication backends will change depending on the backend in
use.

.. seealso::

   * `Django user authentication
     <https://docs.djangoproject.com/en/dev/topics/auth/>`_: the official
     documentation for the user authentication system in Django.
   * `Django authentication packages
     <http://www.djangopackages.com/grids/g/authentication/>`_: an unofficial
     list of packages for user authentication.
