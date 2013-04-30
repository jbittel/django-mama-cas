.. _forms:

.. module:: mama_cas.forms

Forms
=====

django-mama-cas includes a form class implementing standard username and
password authentication. In most cases, this will be the form of
authentication required. Trust authentication can be used with CAS, but the
requirements will be highly implementation dependent.

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

   ``service``
      The service the client is attempting to access, typically represented
      as a URL. This is a hidden, optional field and is automatically added
      to the form when present.

   The form's ``clean()`` method attempts authentication against the
   configured authentication backends and verifies the user account is active.
   If either check fails, a ``FormValidation`` error is raised with an
   appropriate error message.

The following form classes all inherit from ``LoginForm``, providing
additional or alternate behavior during the login process.

.. class:: LoginFormWarn

   A subclass of :class:`LoginForm` which adds one additional, optional field:

   ``warn``
      A checkbox that indicates whether or not the single sign-on process
      should be transparent. This causes the user to be notified before being
      authenticated to another service and provides the option to continue
      the authentication attempt or end the single sign-on session.

.. class:: LoginFormEmail

   A subclass of :class:`LoginForm` which adds no additional fields but
   performs additional cleanup on the ``username`` field. If an email address
   is provided for the username, it extracts only the username portion of the
   string.

Additional Forms
----------------

.. class:: WarnForm

   This form is used when warning the user that an authentication attempt is
   taking place. It contains no visible form fields, but contains two hidden
   fields, ``service`` and ``gateway``. This allows the values of these
   parameters to be passed through the warning process.
