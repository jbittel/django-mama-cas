django-mama-cas
===============

django-mama-cas is a Django `Central Authentication Service (CAS)`_ single
sign-on server. It implements the CAS 1.0 and 2.0 protocols, as well as some
commonly used extensions to the specification.

CAS is a single sign-on protocol that allows a user to access multiple
applications after providing their credentials a single time. It utilizes
security tickets, unique text strings generated and validated by the server,
allowing applications to authenticate a user without direct access to the
user's credentials (typically a user ID and password).

The source code can be found at `github.com/jbittel/django-mama-cas`_, and is
the preferred location for contributions, suggestions and bug reports.
Documentation is available at `django-mama-cas.readthedocs.org`_.

Quickstart
----------

Install with `pip`_::

   pip install django-mama-cas

Add to ``INSTALLED_APPS``::

   INSTALLED_APPS += ('mama_cas',)

Add to the URLconf::

   urlpatterns += patterns('', (r'', include('mama_cas.urls')))

Upgrade
-------

Upgrade with `pip`_::

   pip install django-mama-cas --upgrade

Before upgrading, see the `changelog`_ for any backward incompatible
changes or other important upgrade notes.

.. _Central Authentication Service (CAS): http://www.jasig.org/cas
.. _github.com/jbittel/django-mama-cas: https://github.com/jbittel/django-mama-cas
.. _django-mama-cas.readthedocs.org: http://django-mama-cas.readthedocs.org/
.. _pip: http://www.pip-installer.org/
.. _changelog: http://django-mama-cas.readthedocs.org/en/latest/changelog.html
