MamaCAS
=======

MamaCAS is a Django `Central Authentication Service (CAS)`_ single sign-on
server. It implements the CAS 1.0 and 2.0 protocols, as well as some commonly
used extensions to the specification.

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

   $ pip install django-mama-cas

Add to ``INSTALLED_APPS``::

   INSTALLED_APPS += ('mama_cas',)

Add to the URLconf::

   urlpatterns += patterns('', (r'', include('mama_cas.urls')))

See the full `installation instructions`_ for further details.

Upgrade
-------

Upgrade with `pip`_::

   $ pip install django-mama-cas --upgrade

Before upgrading, see the `changelog`_ for any backward incompatible
changes or other important upgrade notes.

Contributing
------------

Contributions are welcome! The preferred process for changes is by submitting
GitHub pull requests. New code should follow both `PEP8`_ and the `Django
coding style`_, generally respecting the style of the surrounding code. When
appropriate, pull requests should add or update tests, along with any
necessary documentation changes. With any substantial contribution, feel
free to add yourself as a contributor in the AUTHORS file.

Development dependencies can be installed from ``requirements.txt``. Execute
the test suite with::

   $ py.test mama_cas/tests/ --cov=mama_cas --cov-report=html

.. _Central Authentication Service (CAS): http://www.jasig.org/cas
.. _github.com/jbittel/django-mama-cas: https://github.com/jbittel/django-mama-cas
.. _django-mama-cas.readthedocs.org: http://django-mama-cas.readthedocs.org/
.. _pip: http://www.pip-installer.org/
.. _installation instructions: http://django-mama-cas.readthedocs.org/en/latest/installation.html
.. _changelog: http://django-mama-cas.readthedocs.org/en/latest/changelog.html
.. _PEP8: http://www.python.org/dev/peps/pep-0008
.. _Django coding style: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style
