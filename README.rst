MamaCAS
=======

.. image:: https://travis-ci.org/jbittel/django-mama-cas.png?branch=master
    :target: https://travis-ci.org/jbittel/django-mama-cas

MamaCAS is a Django `Central Authentication Service (CAS)`_ single sign-on
and single logout server. It implements the CAS 1.0, 2.0 and 3.0 protocols,
including some of the optional features.

CAS_ is a single sign-on and single logout web protocol that allows a user
to access multiple applications after providing their credentials a single
time. It utilizes security tickets, unique text strings generated and
validated by the server, allowing applications to authenticate a user without
direct access to the user's credentials (typically a user ID and password).

The source code can be found at `github.com/jbittel/django-mama-cas`_, and is
the preferred location for contributions, suggestions and bug reports.
Documentation is available at `django-mama-cas.readthedocs.org`_.

Quickstart
----------

Install with `pip`_::

   $ pip install django-mama-cas

Add to ``INSTALLED_APPS`` and run ``migrate``::

   INSTALLED_APPS += ('mama_cas',)

Include the URLs::

   urlpatterns += [url(r'', include('mama_cas.urls'))]

See the full `installation instructions`_ for details.

Upgrade
-------

Upgrade with `pip`_::

   $ pip install --upgrade django-mama-cas

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

Development dependencies can be installed from ``requirements.txt``.
Execute the test suite with::

   $ py.test

You can use `tox`_ to run the tests against all supported versions of
Python and Django.

.. _Central Authentication Service (CAS):
.. _CAS: https://wiki.jasig.org/display/CAS/Home
.. _github.com/jbittel/django-mama-cas: https://github.com/jbittel/django-mama-cas
.. _django-mama-cas.readthedocs.org: http://django-mama-cas.readthedocs.org/
.. _pip: https://pip.pypa.io/
.. _installation instructions: http://django-mama-cas.readthedocs.org/en/latest/installation.html
.. _changelog: http://django-mama-cas.readthedocs.org/en/latest/changelog.html
.. _PEP8: http://www.python.org/dev/peps/pep-0008
.. _Django coding style: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style
.. _tox: http://tox.testrun.org/
