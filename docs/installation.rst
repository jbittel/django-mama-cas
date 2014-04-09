.. _installation:

Installation
============

Prerequisites
-------------

The primary prerequisite of MamaCAS is `Django`_ itself. Generally speaking,
MamaCAS supports all supported release versions of Django, including LTS
releases. Other versions of Django may work, but are not tested or supported.
See the `Django downloads`_ page for information on downloading and installing
Django.

If you're installing MamaCAS manually, such as from the `GitHub`_ repository,
you'll need to install the Python `requests`_ library.

Installing
----------

Installing the latest release is easiest with `pip`_::

   $ pip install django-mama-cas

To manually install the latest release, download it from `PyPI`_ and install
with::

   $ python setup.py install

If you need the latest development code, clone the active development
repository on `GitHub`_::

   $ git clone git://github.com/jbittel/django-mama-cas.git

Or, download the `tarball`_::

   $ curl -OL https://github.com/jbittel/django-mama-cas/tarball/master

Configuring
-----------

First, add MamaCAS to the ``INSTALLED_APPS`` setting within your project's
``settings.py`` (or equivalent) file::

   INSTALLED_APPS = (
       # ...existing apps...
       'mama_cas',
   )

Once added, run ``manage.py syncdb`` to create the required database tables.

URL paths
~~~~~~~~~

MamaCAS includes a Django URLconf that provides the required CAS URIs (e.g.
``login/``, ``logout/``, ``validate/``, etc.). They are located in
``mama_cas.urls`` and can be included directly in your project's root
``URLconf`` with the following::

   urlpatterns = patterns('',
       # ...existing urls...
       (r'', include('mama_cas.urls')),
   )

This makes the CAS server available at the top level of your project's
URL (e.g. ``http://example.com/login``). To make the server available in a
subdirectory, add the path to the regular expression. For example, to access
the server at ``http://example.com/cas/login``::

   urlpatterns = patterns('',
       # ...existing urls...
       (r'^cas/', include('mama_cas.urls')),
   )

Sessions
~~~~~~~~

MamaCAS relies on standard Django sessions to govern single sign-on sessions.
There are two Django session settings that typically ought to be changed from
their defaults:

   `SESSION_COOKIE_AGE`_
      It is recommended this be set shorter than the default of two weeks.
      This setting controls the duration of single sign-on sessions as well
      as the duration of proxy-granting tickets.

   `SESSION_EXPIRE_AT_BROWSER_CLOSE`_
      This should be set to ``True`` to conform to the CAS specification.
      Note that some browsers can be configured to retain cookies across
      browser restarts, even for cookies set to be removed on browser close.

For more information on how sessions work within Django, read the `session
documentation`_.

Authenticating
--------------

One or more `authentication backends`_ must be `installed and configured`_
based on your authoritative authentication sources. MamaCAS does not
perform authentication itself, but relies on the active authentication
backends. The process of installing and configuring authentication backends
will change depending on the individual backend.

.. seealso::

   * Django `user authentication documentation`_
   * `Authentication packages`_ for Django

.. _Django: http://www.djangoproject.com/
.. _Django downloads: https://www.djangoproject.com/download/
.. _requests: http://python-requests.org/
.. _pip: http://www.pip-installer.org/
.. _PyPI: https://pypi.python.org/pypi/django-mama-cas/
.. _GitHub: https://github.com/jbittel/django-mama-cas
.. _tarball: https://github.com/jbittel/django-mama-cas/tarball/master
.. _SESSION_COOKIE_AGE: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SESSION_COOKIE_AGE
.. _SESSION_EXPIRE_AT_BROWSER_CLOSE: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SESSION_EXPIRE_AT_BROWSER_CLOSE
.. _session documentation: https://docs.djangoproject.com/en/dev/topics/http/sessions/
.. _authentication backends: http://pypi.python.org/pypi?:action=browse&c=475&c=523
.. _installed and configured: https://docs.djangoproject.com/en/dev/topics/auth/customizing/#specifying-authentication-backends
.. _user authentication documentation: https://docs.djangoproject.com/en/dev/topics/auth/
.. _Authentication packages: http://www.djangopackages.com/grids/g/authentication/
