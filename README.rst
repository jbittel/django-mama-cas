django-mama-cas
===============

django-mama-cas is a CAS server single sign-on application for Django,
implementing the popular CAS server protocol in Python. It implements the CAS
1.0 and 2.0 specifications, as well as some commonly used extensions to the
core protocol. It is designed with several key attributes in mind:

   * Simple installation and configuration
   * Integrates with an existing Python ecosystem
   * Easily use or write Django applications for authentication

The source code can be found at `github.com/jbittel/django-mama-cas`_, and is
the preferred location for contributions, suggestions and bug reports.

Quick Start
-----------

Install with `pip`_::

   pip install django-mama-cas

Add to ``INSTALLED_APPS``::

   INSTALLED_APPS += ('mama_cas',)

Add to the URLconf::

   urlpatterns += patterns('', (r'', include('mama_cas.urls')))

For full installation and configuration instructions, see the local
docs/installation.rst file or read the documentation online at
`django-mama-cas.readthedocs.org`_.

Upgrading
---------

Upgrade with `pip`_::

   pip install django-mama-cas --upgrade

Before upgrading, see the `changelog`_ for any backward incompatible
changes or other important upgrade notes.

.. _github.com/jbittel/django-mama-cas: https://github.com/jbittel/django-mama-cas
.. _pip: http://www.pip-installer.org/
.. _django-mama-cas.readthedocs.org: http://django-mama-cas.readthedocs.org/.
.. _changelog: http://django-mama-cas.readthedocs.org/en/latest/changelog.html
