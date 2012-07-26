.. django-mama-cas documentation master file, created by
   sphinx-quickstart on Fri Jun 15 14:45:35 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-mama-cas 0.1 documentation
=================================

django-mama-cas is an implementation of the CAS protocol specification,
intended to provide single sign-on server functionality. It provides the
required CAS URIs to receive and respond to CAS authentication and validation
attempts.

`Central Authentication Service (CAS)
<http://en.wikipedia.org/wiki/Central_Authentication_Service>`_ is an
HTTP-based `protocol <http://www.jasig.org/cas/protocol>`_ that provides
single sign-on functionality. It provides both a credential requestor and
acceptor, as well as a validator for services to check for an existing single
sign-on session.  This allows web services to authenticate a user without
having access to the user's credentials.

To begin, please read the :ref:`getting started <getting-started>` document
for information on how to install and configure django-mama-cas.

Contents:

.. toctree::
   :maxdepth: 1

   getting-started
   templates
   forms
   management-commands
   protocol

Note that the current release of django-mama-cas is an early alpha release and
is not intended for production deployment. Testing, patches and feedback are
much appreciated!
