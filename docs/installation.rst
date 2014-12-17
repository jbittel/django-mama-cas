.. _installation:

Installation
============

Prerequisites
-------------

The primary prerequisite of MamaCAS is `Django`_ itself. MamaCAS supports the
last two major release versions of Django and the current LTS release,
generally following Django's `support policy`_. Other versions of Django may
work, but are not officially tested or supported. See the `Django downloads`_
page for information on downloading and installing Django.

If you're installing MamaCAS manually, such as from the `GitHub`_ repository,
you'll need to install the `Requests`_ and `defusedxml`_ libraries. The
optional `gevent`_ module may also be installed to enable asynchronous
single sign-out requests.

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

Configuring
-----------

First, add MamaCAS to the ``INSTALLED_APPS`` setting within your project's
``settings.py`` (or equivalent) file::

   INSTALLED_APPS = (
       # ...existing apps...
       'mama_cas',
   )

Once added, run ``manage.py migrate`` to create the required database tables.

URL paths
~~~~~~~~~

Include the required CAS URL endpoints in your project's root ``URLconf``
with the following::

   urlpatterns = patterns('',
       # ...existing urls...
       (r'', include('mama_cas.urls')),
   )

This makes the CAS server available at the top level of your project's
URL (e.g. ``http://example.com/login``). To add a subpath to the CAS root
(e.g. ``http://example.com/cas/login``) add the path to the URL regular
expression::

   urlpatterns = patterns('',
       # ...existing urls...
       (r'^cas/', include('mama_cas.urls')),
   )

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
.. _support policy: https://docs.djangoproject.com/en/dev/internals/release-process/
.. _Django downloads: https://www.djangoproject.com/download/
.. _Requests: http://python-requests.org/
.. _defusedxml: https://bitbucket.org/tiran/defusedxml
.. _gevent: http://www.gevent.org/
.. _pip: https://pip.pypa.io/
.. _PyPI: https://pypi.python.org/pypi/django-mama-cas/
.. _GitHub: https://github.com/jbittel/django-mama-cas
.. _tarball: https://github.com/jbittel/django-mama-cas/tarball/master
.. _authentication backends: http://pypi.python.org/pypi?:action=browse&c=475&c=523
.. _installed and configured: https://docs.djangoproject.com/en/dev/topics/auth/customizing/#specifying-authentication-backends
.. _user authentication documentation: https://docs.djangoproject.com/en/dev/topics/auth/
.. _Authentication packages: http://www.djangopackages.com/grids/g/authentication/
