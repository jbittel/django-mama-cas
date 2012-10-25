.. _protocol:

CAS protocol
============

The official CAS protocol specification can be found at
http://www.jasig.org/cas/protocol. Where appropriate, comments within the
code include numbers in parenthesis (e.g. ``(2.3)``) corresponding to the
section number within the CAS protocol documentation where that functionality
is described. Additionally, views are labeled with a CAS version number in
brackets (e.g. ``[CAS 2.0]``) corresponding to the CAS version that defines
that particular URI.

.. seealso::

   * `CAS Protocol <http://www.jasig.org/cas/protocol>`_
   * `CAS User Manual <https://wiki.jasig.org/display/CASUM/Home>`_

Authentication process
----------------------

A quick summary of how the authentication process works might be helpful in
understanding how these pieces work together. Obviously, a lot of detail is
skipped here that is necessary for a complete understanding of how the login
process works.

**CAS 1.0 authentication process**
   To begin, an unauthenticated client initiates a login request from a CAS
   enabled service. The service redirects the login request to ``/login``,
   which is acting as a credential requestor. Along with the login request,
   the service URL is passed as a GET parameter. The CAS server finds no
   existing session for the client, and therefore displays a login form. The
   client enters appropriate credentials and submits the form back to
   ``/login``, which is now acting as a credential acceptor. If the credentials
   are valid, a service ticket is generated specific to the service URL
   provided and the client is redirected back to the service URL with the
   service ticket appended to the request.

   Now that the service has received a service ticket, it makes an additional
   request to ``/validate`` to verify the validity of the service ticket that
   was received. Whether or not this validation succeeds, the service ticket
   is used up and is invalid for any future validation attempts. If the
   service ticket validates, the user is now successfully authenticated to the
   service.

.. seealso::

   * `CAS 1 Architecture <http://www.jasig.org/cas/cas1-architecture>`_

**CAS 2.0 authentication process**
   When using CAS 2.0, the first step in the authentication process occurs
   identically to CAS 1.0. However, once the service receives the service
   ticket, it instead makes a request to either ``/serviceValidate`` or
   ``/proxyValidate`` to validate the service ticket.

   If the service desires a proxy ticket, it will pass a proxy callback URL
   as a parameter to the validator. If the callback URL is valid, a proxy-
   granting ticket is returned to the service.

   Having obtained a proxy-granting ticket, the service can then issue a
   request to ``/proxy`` to aquire proxy tickets which can then be validated
   through ``/proxyValidate``.

.. seealso::

   * `CAS 2 Architecture <http://www.jasig.org/cas/cas2-architecture>`_
   * `Proxy Authentication <http://www.jasig.org/cas/proxy-authentication>`_

.. _protocol-deviations:

Protocol deviations
-------------------

There are some areas where django-mama-cas deviates from the official CAS
specification to take advantage of built-in Django functionality.

**Login ticket**
   This ticket string created for the login form is passed along with the
   username and password to prevent the replaying of credentials.
   django-mama-cas does not implement login tickets and instead relies on
   the built-in CSRF protection for the login form.

**Ticket-granting ticket**
   This ticket string is stored on the server and keys to a ticket-granting
   cookie provided by the client to identify an existing single sign-on
   session. django-mama-cas does not implement ticket-granting tickets and
   instead uses Django sessions to determine whether or not a single sign-on
   session has been established.

**Custom attributes**
   Custom attributes can be returned along with a CAS 2.0 service or proxy
   validation success. This is not part of the official CAS specification, but
   is widely used in practice.

These changes do not alter the contract between the client, service and CAS
server.
