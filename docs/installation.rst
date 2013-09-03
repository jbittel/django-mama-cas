.. _installation:

Installation
============

Prerequisites
-------------

The primary prerequisite of django-mama-cas is `Django`_ itself. For
django-mama-cas |version|, Django 1.4 or later is required. Earlier versions
of Django may work, but are not tested or supported. See the `Django
downloads`_ page for information on downloading and installing Django.

If you're installing django-mama-cas manually, such as from the `GitHub`_
repository, you'll need to install the Python `requests`_ library. Install
it with::

   pip install requests

Installing
----------

There are several different ways to install django-mama-cas, depending on your
preferences and needs. In all cases, it is recommended to run the installation
within a `virtualenv`_ for isolation from other system packages.

Via pip
~~~~~~~

The easiest way to install it is with `pip`_::

   pip install django-mama-cas

Via a downloaded package
~~~~~~~~~~~~~~~~~~~~~~~~

If you cannot access pip or prefer to install the package manually, download
it from `PyPI`_. Extract the downloaded archive and install it with::

   python setup.py install

Via GitHub
~~~~~~~~~~

To stay current with the latest development, clone the active development
repository on `GitHub`_::

   git clone git://github.com/jbittel/django-mama-cas.git

If you don't want a full git repository, download the latest code from GitHub
as a `tarball`_.

Configuring
-----------

First, add django-mama-cas to the ``INSTALLED_APPS`` setting within your
project's ``settings.py`` (or equivalent) file::

   INSTALLED_APPS = (
       # ...existing apps...
       'mama_cas',
   )

Once added, run ``manage.py syncdb`` to create the required database tables.

URL paths
~~~~~~~~~

django-mama-cas includes a Django ``URLconf`` that provides the required CAS
URIs (e.g. ``login/``, ``logout/``, ``validate/``, etc.). They are located in
``mama_cas.urls`` and can be included directly in your project's root
``URLconf`` with the following::

   urlpatterns = patterns('',
       # ...existing urls...
       (r'', include('mama_cas.urls')),
   )

This makes the CAS server available at the top level of your project's
URL. If you prefer to access it within a subdirectory, add a base to the
included URLs. For example, to make the CAS server available under the
``/cas/`` directory, use this instead::

   (r'^cas/', include('mama_cas.urls')),

Changing the URLs within ``mama_cas.urls`` is not recommended as it will
likely break standard CAS behavior.

Sessions
~~~~~~~~

django-mama-cas relies on standard Django sessions to govern single sign-on
sessions. There are two Django session settings that will likely need to be
changed from their defaults:

   `SESSION_COOKIE_AGE`_
      It is recommended this be set shorter than the default of two weeks.

   `SESSION_EXPIRE_AT_BROWSER_CLOSE`_
      This should be set to ``True`` to conform to the CAS specification.

For information on how sessions work within Django, read the `session
documentation`_. These settings ought to be configured to fit your environment
and security requirements.

Authentication
--------------

At least one `authentication backend`_ must be `installed and configured`_,
depending on your authoritative authentication source. django-mama-cas does
not perform authentication itself, but relies on the active authentication
backends for that task. The process of configuring authentication backends
will change depending on the individual backend.

.. seealso::

   * Django `user authentication documentation`_
   * `Authentication packages`_ for Django

.. _Django: http://www.djangoproject.com/
.. _Django downloads: https://www.djangoproject.com/download/
.. _requests: http://python-requests.org/
.. _virtualenv: http://www.virtualenv.org/
.. _pip: http://www.pip-installer.org/
.. _PyPI: https://pypi.python.org/pypi/django-mama-cas/
.. _GitHub: https://github.com/jbittel/django-mama-cas
.. _tarball: https://github.com/jbittel/django-mama-cas/tarball/master
.. _SESSION_COOKIE_AGE: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SESSION_COOKIE_AGE
.. _SESSION_EXPIRE_AT_BROWSER_CLOSE: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SESSION_EXPIRE_AT_BROWSER_CLOSE
.. _session documentation: https://docs.djangoproject.com/en/dev/topics/http/sessions/
.. _authentication backend: http://pypi.python.org/pypi?:action=browse&c=475&c=523
.. _installed and configured: https://docs.djangoproject.com/en/dev/topics/auth/customizing/#specifying-authentication-backends
.. _user authentication documentation: https://docs.djangoproject.com/en/dev/topics/auth/
.. _Authentication packages: http://www.djangopackages.com/grids/g/authentication/
