.. _getting-started:

Getting started
===============

Prerequisites
-------------

The only prerequesite of django-mama-cas is `Django
<http://www.djangoproject.com>`_ itself. For django-mama-cas |version|, Django
1.4 or later is required. Earlier versions of Django may work, but are not
tested or supported.

You will also need an authentication backend installed and configured, which
will change depending on your authoritative authentication source.

Installing django-mama-cas
--------------------------

Via pip
~~~~~~~

The easiest way to install django-mama-cas is by using pip. Simply type::

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

Configure session expiration
Configure session caching?
Other available settings and their defaults

URL paths
~~~~~~~~~

django-mama-cas includes a Django ``URLconf`` that provides the required CAS
URIs (e.g. login, logout, validate). They are located in ``mama_cas.urls``
and can be included directly in your project's root ``URLconf``. For example::

   (r'', include('mama_cas.urls')),

This would make the CAS server available at the top level of your project's
URL. If this is not the desired behavior, you can add a prefix to the included
URLs. For example, if you wished the CAS server to be available under the
``/cas/`` prefix you would use::
   
   (r'^cas/', include('mama_cas.urls')),

You would also need to ensure that all CAS enabled services are configured
with a prefix that matches your configuration here. Changing the CAS URLs
within ``mama_cas.urls`` is not recommended as they are specific to the HTTP
contract specification and will likely break the CAS behavior.

Templates
~~~~~~~~~

django-mama-cas comes with basic templates implementing standard username and
password authentication. They are intentionally generic and extendable to
serve as a starting point for your own templates, but can also be replaced
wholesale.

Read the :ref:`template documentation <templates>` for more information on the
included templates.

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
