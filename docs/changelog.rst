.. _changelog:

Changelog
=========

This is an overview of all notable changes between each release of
django-mama-cas. Backwards incompatible changes or other potential problems
are noted here, so it's great reading material before upgrading. If this is
not enough detail, try the complete `commit history
<https://github.com/jbittel/django-mama-cas/commits/>`_.

**django-mama-cas 0.4.0**
   * Implement service management setting
   * Improve logging levels and specificity
   * Fix ticket expiration setting name
   * Fix PGTs expiring according to the standard expiration value

**django-mama-cas 0.3.0**
   * Implement warn parameter for the credential acceptor
   * Parse XML in tests to better check validity
   * Fix partial logout with the renew parameter
   * Implement custom attributes returned with a validation success

**django-mama-cas 0.2.0**
   * Implement internationalization
   * Add proxy ticket validation
   * Substantial improvements to the test suite
   * Add traversed proxies to proxy validation response
   * Add form class to extract usernames from email addresses

Versioning follows the `semantic versioning <http://semver.org/>`_ scheme for
more consistent dependency behavior.
