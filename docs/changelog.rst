.. _changelog:

Changelog
=========

These are the notable changes for each django-mama-cas release.  Backwards
incompatible changes or other upgrade issues are also described here.  For
additional detail, read the complete `commit history`_.  From version 0.4.0
and following, version numbers follow the `semantic versioning`_ scheme.

**django-mama-cas 0.6.0** ``[2013-09-04]``
   * Add Python 3 compatibility
   * Add a setting to follow provided logout URLs

**django-mama-cas 0.5.0** ``[2013-04-29]``
   * Fix login template not validating data properly
   * Respect REQUESTS_CA_BUNDLE environment variable
   * Fix login failures with case-sensitive authentication backends
   * Support for Django 1.5 custom User models

**django-mama-cas 0.4.0** ``[2013-01-31]``
   * Implement service management setting
   * Improve logging levels and specificity
   * Fix ticket expiration setting name
   * Fix PGTs expiring according to the standard expiration value

**django-mama-cas 0.3** ``[2012-10-26]``
   * Implement warn parameter for the credential acceptor
   * Parse XML in tests to better check validity
   * Fix partial logout with the renew parameter
   * Implement custom attributes returned with a validation success

**django-mama-cas 0.2** ``[2012-07-12]``
   * Implement internationalization
   * Add proxy ticket validation
   * Substantial improvements to the test suite
   * Add traversed proxies to proxy validation response
   * Add form class to extract usernames from email addresses

.. _commit history: https://github.com/jbittel/django-mama-cas/commits/
.. _semantic versioning: http://semver.org/
