.. _changelog:

Changelog
=========

Listed are the high-level, notable changes for each MamaCAS release.
Backwards incompatible changes or other upgrade issues are also described
here. For additional detail, read the complete `commit history`_. From
version 0.4.0 and following, version numbers follow the `semantic
versioning`_ scheme.

**django-mama-cas 0.8.1** ``[2014-05-20]``
   * Fix validation response not returning PGTIOU

**django-mama-cas 0.8.0** ``[2014-05-09]``
   * Add single sign-out functionality
   * Add callback for returning custom user attributes
   * Fix support for custom user models with no ``username`` field

**django-mama-cas 0.7.1** ``[2014-01-28]``
   * Fix Python 2.6 compatibility

**django-mama-cas 0.7.0** ``[2014-01-21]``
   * Generate CAS 2.0 XML responses instead of using templates
   * Expire PGTs according to SESSION_COOKIE_AGE
   * Change ticket created field to expiry date
   * Change ticket expiration duration to seconds
   * Fix ticket cleanup cascading to valid tickets

   .. warning::

      The ``created`` field on ``ServiceTicket``, ``ProxyTicket`` and
      ``ProxyGrantingTicket`` was renamed to ``expires``. If upgrading,
      you must ensure this field is renamed accordingly.

   .. warning::

      The ``MAMA_CAS_TICKET_EXPIRE`` setting previously specified ticket
      expiration in minutes and defaulted to *5*. Now the setting is
      specified in seconds and defaults to *90*.

**django-mama-cas 0.6.1** ``[2013-11-11]``
   * Django 1.6 compatibility
   * Handle exceptions raised by authentication backends

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
