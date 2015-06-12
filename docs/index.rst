.. django-mama-cas documentation master file, created by
   sphinx-quickstart on Fri Jun 15 14:45:35 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction
============

MamaCAS is a Django `Central Authentication Service (CAS)`_ single sign-on
and single logout server. It implements the CAS 1.0, 2.0 and 3.0 protocols,
including some of the optional features.

CAS_ is a single sign-on and single logout web protocol that allows a user
to access multiple applications after providing their credentials a single
time. It utilizes security tickets, unique text strings generated and
validated by the server, allowing applications to authenticate a user without
direct access to the user's credentials (typically a user ID and password).

The source code can be found at `github.com/jbittel/django-mama-cas`_, and is
the preferred location for contributions, suggestions and bug reports.

Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   settings
   security
   templates
   management-commands
   forms
   protocol
   changelog

.. _Central Authentication Service (CAS):
.. _CAS: http://jasig.github.io/cas/
.. _github.com/jbittel/django-mama-cas: https://github.com/jbittel/django-mama-cas
