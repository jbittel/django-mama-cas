.. _changelog:

Changelog
=========

Listed are the high-level, notable changes for each MamaCAS release.
Backwards incompatible changes or other upgrade issues are also described
here. For additional detail, read the complete `commit history`_. From
version 0.4.0 and following, version numbers follow the `semantic
versioning`_ scheme.

**django-mama-cas 2.1.0** ``[2016-09-02]``
   * Add Django 1.10 compatibility
   * Add per-service configuration with ``MAMA_CAS_SERVICES``
   * Add allowing/disallowing proxying for each service
   * Add pgtUrl identifier pattern validation
   * Add configurable logout URL for each service
   * Add ``checkservice`` management command for testing service identifiers
   * Reverted logout ``url`` parameter removal for older client compatibility
   * Fix direct access of ``User`` model in test suite

   .. warning::

      ``MAMA_CAS_VALID_SERVICES``, ``MAMA_CAS_ATTRIBUTE_CALLBACKS``,
      and ``MAMA_CAS_ENABLE_SINGLE_SIGN_OUT`` have been deprecated in
      favor of per-service configuration with ``MAMA_CAS_SERVICES``.

**django-mama-cas 2.0.1** ``[2016-01-04]``
   * Fix SLO request encoding

**django-mama-cas 2.0.0** ``[2015-12-17]``
   * Fix Django 1.9 compatibility
   * Drop support for unsupported Django versions
   * Remove ``url`` parameter to ``/logout``
   * Change service URL comparison to be more strict
   * Fix pgtURL validation not checking against valid services

   .. warning::

      Support has been dropped for Django 1.4, 1.6 and 1.7, matching Django's
      supported versions policy.

**django-mama-cas 1.2.0** ``[2015-08-21]``
   * Add new CAS 3 endpoints as aliases
   * Update CAS validation error response codes
   * Fix ``TARGET`` parameter case for /samlValidate
   * Require HTTPS URLs for /samlValidate

**django-mama-cas 1.1.1** ``[2015-05-15]``
   * Fix exception when inserting Unicode parameters

**django-mama-cas 1.1.0** ``[2015-04-01]``
   * Made defusedxml requirement optional
   * Changed stock templates to use Bootstrap
   * Enforce CSRF protection on login form
   * Fix South migrations for user model foreign keys

**django-mama-cas 1.0.0** ``[2014-12-22]``
   * Add Django and South database migrations
   * Add example user attribute callbacks
   * Fix error when supplying non-string attribute values
   * Remove ``MAMA_CAS_USER_ATTRIBUTES`` and ``MAMA_CAS_PROFILE_ATTRIBUTES``

   .. warning::

      ``MAMA_CAS_USER_ATTRIBUTES`` and ``MAMA_CAS_PROFILE_ATTRIBUTES``
      have been removed. Use ``MAMA_CAS_ATTRIBUTE_CALLBACKS`` instead.

**django-mama-cas 0.10.0** ``[2014-10-13]``
   * Default the asychronous concurrency level to ``2``
   * Improve test configuration and output

**django-mama-cas 0.9.0** ``[2014-08-07]``
   * Add support for CAS 3.0 features
   * Allow multiple custom attribute callbacks
   * Use gevent for asynchronous single sign-out requests, if available
   * Fix error when a malformed username was provided
   * Fix logout occurring for a renew request
   * Fix redirects not checking for a valid URL
   * Improve removal of invalid tickets
   * Default ``MAMA_CAS_FOLLOW_LOGOUT_URL`` to ``True``
   * Deprecate ``MAMA_CAS_USER_ATTRIBUTES`` and ``MAMA_CAS_PROFILE_ATTRIBUTES``

   .. warning::

      The ``MAMA_CAS_ATTRIBUTES_CALLBACK`` setting was renamed to
      ``MAMA_CAS_ATTRIBUTE_CALLBACKS`` and now takes a tuple of dotted
      paths to callables.

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
