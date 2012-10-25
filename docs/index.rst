.. django-mama-cas documentation master file, created by
   sphinx-quickstart on Fri Jun 15 14:45:35 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-mama-cas documentation
=============================

django-mama-cas is a Python implementation of the `Central Authentication
Service (CAS) <http://en.wikipedia.org/wiki/Central_Authentication_Service>`_
server protocol, providing single sign-on server functionality as a Django
application. It implements the current CAS specification to handle CAS
authentication and validation requests.

CAS is an HTTP-based protocol that provides single sign-on functionality to web
services. It operates using tickets, unique text strings that are provided and
validated by the server, allowing web services to authenticate a user without
having access to the user's credentials. The :ref:`protocol <protocol>` page
has more information about CAS and this implementation of it.

Most likely, you'd like to know how to :ref:`get started <getting-started>`.

You might also be interested in :ref:`what's changed <changelog>`.

Contents
--------

.. toctree::
   :maxdepth: 1

   getting-started
   changelog
   templates
   management-commands
   forms
   protocol
