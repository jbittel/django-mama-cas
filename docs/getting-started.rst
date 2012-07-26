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

You will also need an `authentication backend
<https://docs.djangoproject.com/en/dev/topics/auth/#specifying-authentication-backends>`_
installed and configured, which will change depending on your authoritative
authentication source.

Installing django-mama-cas
--------------------------

Via pip
~~~~~~~

The easiest way to install django-mama-cas is using pip. Simply type::

   pip install django-mama-cas

Via a downloaded package
~~~~~~~~~~~~~~~~~~~~~~~~

You can also manually download django-mama-cas from
`GitHub <https://github.com/jbittel/django-mama-cas>`_. Extract the downloaded
archive and install it with::

   python setup.py install

Configuration
-------------

Once installed, add django-mama-cas to your project by modifying the
``INSTALLED_APPS`` setting to insert this line::

   'mama_cas',

Once django-mama-cas is added to the project, run ``python manage.py syncdb``
to install the required database tables.

Sessions
~~~~~~~~

django-mama-cas relies on the built-in Django sessions to control session
storage and expiration. To understand how sessions work within Django,
read the `session documentation
<https://docs.djangoproject.com/en/dev/topics/http/sessions/>`_. There are
three particular session settings that control where sessions are stored and
how they are expired:

   * `SESSION_ENGINE
     <https://docs.djangoproject.com/en/dev/topics/http/sessions/#session-engine>`_

   * `SESSION_COOKIE_AGE
     <https://docs.djangoproject.com/en/dev/topics/http/sessions/#session-cookie-age>`_

   * `SESSION_EXPIRE_AT_BROWSER_CLOSE
     <https://docs.djangoproject.com/en/dev/topics/http/sessions/#session-expire-at-browser-close>`_

URL paths
~~~~~~~~~

django-mama-cas includes a Django ``URLconf`` that provides the required CAS
URIs (e.g. login, logout, validate). They are located in ``mama_cas.urls``
and can be included directly in your project's root ``URLconf``. For example::

   (r'', include('mama_cas.urls')),

This would make the CAS server available at the top level of your project's
URLs. If this is not the desired location, you can add a base to the included
URLs. For example, if you wished the CAS server to be available under the
``/cas/`` base you would use::
   
   (r'^cas/', include('mama_cas.urls')),

All CAS enabled services need to be configured according to the URL settings
here. Changing the CAS URLs within ``mama_cas.urls`` is not recommended as
that will likely break CAS behavior.

Templates
~~~~~~~~~

django-mama-cas comes with a basic template implementing standard username and
password authentication. It will work as provided, but is intended to be
extended or replaced according to your needs.

Read the :ref:`template documentation <templates>` for more information on the
included template and customization.

Authentication
--------------

django-mama-cas does not perform any authentication itself. It relies on the
configured Django authentication backends for that task. The process of
configuring your authentication backend will change depending on the backend
in use.

.. seealso::

   * `Django user authentication
     <https://docs.djangoproject.com/en/dev/topics/auth/>`_: the official
     documentation for the user authentication system in Django.

   * `django-ldap <https://bitbucket.org/psagers/django-auth-ldap/>`_: an
     authentication backend that authenticates against an LDAP service.
