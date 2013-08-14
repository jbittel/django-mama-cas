.. _protocol:

CAS Protocol
============

The official CAS protocol specification can be found at
http://www.jasig.org/cas/protocol. Where appropriate, comments within the
code include numbers in parenthesis (e.g. ``(2.3)``) corresponding to the
section number within the CAS protocol documentation where that functionality
is described. Additionally, views are labeled with a CAS version number in
brackets (e.g. ``[CAS 2.0]``) corresponding to the CAS version that defines
that particular URI.

CAS 1.0 is primarily a text-based protocol that returns a simple "yes" or "no"
response indicating a validation success or failure. CAS 2.0 returns XML
fragments for validation responses and is capable of including a great deal of
additional data in the process.

.. seealso::

   * `CAS Protocol`_
   * `CAS User Manual`_
   * `CAS 1 Architecture`_
   * `CAS 2 Architecture`_
   * `Proxy Authentication`_

.. _CAS Protocol: http://www.jasig.org/cas/protocol
.. _CAS User Manual: https://wiki.jasig.org/display/CASUM/Home
.. _CAS 1 Architecture: http://www.jasig.org/cas/cas1-architecture
.. _CAS 2 Architecture: http://www.jasig.org/cas/cas2-architecture
.. _Proxy Authentication: http://www.jasig.org/cas/proxy-authentication

Protocol Deviations
-------------------

There are some areas where django-mama-cas deviates from the official CAS
specification to take advantage of built-in Django functionality. These
changes do not alter the contract between the client, service and CAS server.

**Login ticket (3.5)**
   This ticket string created for the login form is passed along with the
   username and password to prevent the replaying of credentials.
   django-mama-cas does not implement login tickets and instead relies on the
   built-in CSRF protection for the login form.

**Ticket-granting ticket (3.6)**
   This ticket string is stored on the server and keys to a ticket-granting
   cookie provided by the client to identify an existing single sign-on
   session. django-mama-cas does not implement ticket-granting tickets and
   instead uses Django sessions to determine whether or not a single sign-on
   session has been established.

**Custom attributes**
   User attributes can be returned along with a CAS 2.0 service or proxy
   validation success. This is not part of the official CAS specification, but
   is widely used in practice.

**Follow logout url**
   Setting ``MAMA_CAS_FOLLOW_LOGOUT_URL`` to ``True`` alters the server's
   behavior at logout from the CAS specification. Depending on the services
   configured for CAS usage, this change can provide a more expected logout
   behavior.
