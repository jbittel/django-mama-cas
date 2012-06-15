.. _protocol:

CAS protocol
============

Protocol specification
----------------------

The official CAS protocol specification can be found at
<http://www.jasig.org/cas/protocol>. Currently django-mama-cas only supports
the CAS 1.0 protocol, although 2.0 support is planned for the future.

**Basic CAS 1.0 authentication process**
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

   This process can become more complicated when renew or gateway parameters
   are provided by the service, as they alter the behavior of the credential
   requestor. For further details of how the protocol works, read the
   `official specification <http://www.jasig.org/cas/protocol>`_.

.. _protocol-deviations:

Protocol deviations
-------------------

There are a few areas where django-mama-cas deviates from the official CAS
specification to take advantage of built-in Django functionality.

**Login ticket**
   According to the specification, this is a string created for the login
   form and is passed along with the username and password to prevent the
   replaying of credentials. django-mama-cas does not implement login
   tickets and instead relies on the built-in CSRF protection for the login
   form.

**Ticket granting ticket**
   This is intended to be a string stored on the server that keys to
   a ticket-granting cookie provided by the client for successful single
   sign-on authentication. django-mama-cas does not implement ticket
   granting tickets and instead uses Django sessions to determine whether or
   not a single sign-on session has already been established when a service
   ticket request is made.

None of these changes alter the contract between the service and the CAS
server. They only affect the internals of the server itself.
