.. _protocol:

CAS Protocol
============

The official CAS protocol specification can be found at
http://www.jasig.org/cas/protocol. Where appropriate, docstrings and other
documentation include numbers in parenthesis (e.g. ``(2.3)``) corresponding
to the section number within the CAS protocol documentation where that
functionality is described. Additionally, views are labeled with a CAS version
number in brackets (e.g. ``[CAS 2.0]``) corresponding to the CAS version that
defines that particular URI.

CAS 1.0 is a plain text protocol that returns a simple "yes" or "no" response
indicating a ticket validation success or failure. CAS 2.0 returns XML
fragments for validation responses and can include a great deal of additional
data within the response.

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

In some areas MamaCAS deviates from the official CAS specification to
take advantage of built-in Django behavior or offer additional functionality.
These changes do not alter the contract between the client, service and CAS
server.

**Login ticket (3.5)**
   This ticket string created for the login form is passed along with the
   username and password to prevent the replaying of credentials. MamaCAS
   does not implement login tickets and instead relies on the built-in CSRF
   protection for the login form.

**Ticket-granting ticket (3.6)**
   This ticket string is stored on the server and keys to a ticket-granting
   cookie provided by the client to identify an existing single sign-on
   session. MamaCAS does not implement ticket-granting tickets, but instead
   uses Django sessions to determine if a single sign-on session has been
   established.

**User attributes**
   User attributes can be included in a CAS 2.0 service or proxy validation
   success using the ``MAMA_CAS_ATTRIBUTES_CALLBACK``,
   ``MAMA_CAS_PROFILE_ATTRIBUTES`` or ``MAMA_CAS_USER_ATTRIBUTES`` settings.
   The inclusion of these attributes is not part of the official CAS
   specification, but is widely used in practice.

**Follow logout URL (2.3.2)**
   Setting ``MAMA_CAS_FOLLOW_LOGOUT_URL`` to ``True`` alters the server's
   behavior at logout from the CAS specification. Depending on the services
   configured for CAS usage, this change may provide a more expected logout
   behavior.
