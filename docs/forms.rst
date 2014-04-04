.. _forms:

.. module:: mama_cas.forms

Forms
=====

MamaCAS includes a form class implementing standard username and password
authentication. In most cases, this will be the form of authentication
required. Trust authentication can be used with CAS, but the requirements
will be highly implementation dependent.

Authentication Forms
--------------------

.. class:: LoginForm

   This is the base form for handling standard username and password
   authentication credentials. It contains the following fields:

   ``username``
      The username of the client requesting authentication. This field is
      required.

   ``password``
      The password of the client requesting authentication. This field is
      required.

   ``warn``
      A checkbox for configuring transparency of the single sign-on
      process. If checked, the user will be notified before being
      authenticated to subsequent services. This field will only be
      displayed if ``MAMA_CAS_ALLOW_AUTH_WARN`` is enabled.

   The form's ``clean()`` method attempts authentication against the
   configured authentication backends and verifies the user account is
   active. If authentication fails, a ``FormValidation`` exception is raised
   with an appropriate error message.

Additional Forms
----------------

The following form classes inherit from ``LoginForm``, providing additional
or alternate behavior during the login process.

.. class:: LoginFormEmail

   A subclass of :class:`LoginForm` which performs additional cleanup on the
   ``username`` field. If an email address is provided for the username, only
   the username portion of the string is used for authentication.
