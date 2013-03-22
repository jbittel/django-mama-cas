.. django-mama-cas documentation master file, created by
   sphinx-quickstart on Fri Jun 15 14:45:35 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-mama-cas documentation
=============================

django-mama-cas is a Python implementation of the `Central Authentication
Service (CAS)`_ server protocol, providing single sign-on server functionality
as a Django application. It implements the CAS 1.0 and 2.0 specifications, as
well as some commonly used extensions to the protocol.

CAS is an HTTP-based protocol that provides single sign-on functionality to web
services. It operates using tickets, unique text strings that are provided and
validated by the server, allowing web services to authenticate a user without
having access to the user's credentials.

.. _Central Authentication Service (CAS): http://en.wikipedia.org/wiki/Central_Authentication_Service

Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   settings
   templates
   management-commands
   forms
   protocol
   changelog
