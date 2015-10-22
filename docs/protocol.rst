.. _protocol:

CAS Protocol
============

The official CAS protocol specification can be found at
http://jasig.github.io/cas/. Where appropriate, docstrings and other
documentation include numbers in parenthesis (e.g. ``(2.3)``) corresponding
to the section number within the CAS protocol documentation where that
functionality is described. Additionally, views are labeled with a CAS version
number in brackets (e.g. ``[CAS 2.0]``) corresponding to the CAS version that
defines that particular URI.

CAS 1.0 is a plain text protocol that returns a simple "yes" or "no" response
indicating a ticket validation success or failure. CAS 2.0 returns XML
fragments for validation responses and allows for proxy authentication. CAS
3.0 expands the protocol with additional request parameters and a SAML
response endpoint.

.. seealso::

   * `CAS Protocol`_
   * `CAS User Manual`_
   * `CAS 1 Architecture`_
   * `CAS 2 Architecture`_
   * `Proxy Authentication`_

Protocol Deviations
-------------------

In some areas MamaCAS deviates from the official CAS specification to take
advantage of built-in Django functionality. These changes do not alter the
contract between the client, service and CAS server.

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

.. _CAS Protocol: http://jasig.github.io/cas/4.0.x/protocol/CAS-Protocol.html
.. _CAS User Manual: http://jasig.github.io/cas/
.. _CAS 1 Architecture: https://www.apereo.org/projects/cas/cas-1-architecture
.. _CAS 2 Architecture: https://www.apereo.org/content/cas-2-architecture
.. _Proxy Authentication: https://www.apereo.org/content/why-do-we-need-proxy-authentication
