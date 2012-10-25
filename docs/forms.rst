.. _forms:
.. module:: mama_cas.forms

Forms
=====

Authentication forms
--------------------

django-mama-cas includes a form class for implementing standard username and
password authentication. In most cases, this will be the form of
authentication required. Trust authentication can be used with CAS, but the
requirements are highly implementation dependent.

.. class:: LoginForm

   This is the base form for handling user authentication. It contains the
   following fields:

   ``username``
      The username of the client requesting authentication. The provided
      string is automatically converted to lowercase for consistency. This
      field is required.

   ``password``
      The password of the client requesting authentication. This field is
      required.

   ``service``
      The service the client is attempting to access, typically represented
      as a URL. This is a hidden, optional field and is automatically added
      to the form when provided.

   The form's ``clean()`` method attempts authentication against the configured
   authentication backends and verifies that the user account is active.
   If either check fails, a ``FormValidation`` error is raised with an
   appropriate error message.

   Note that this form deviates slightly from the official CAS protocol
   specification, as documented in :ref:`protocol-deviations`.

The following form classes all inherit from ``LoginForm``, providing additional
or alternate behavior during the login process.

.. class:: LoginFormWarn

   A subclass of :class:`LoginForm` which adds one additional, optional field:

   ``warn``
      A checkbox that indicates whether or not the single sign-on process
      should be transparent. This causes the user to be notified before being
      authenticated to another service and provided the option to continue
      with the authentication attempt or end the single sign-on session.

.. class:: LoginFormEmail

   A subclass of :class:`LoginForm` which adds no additional fields but
   performs additional cleanup on the ``username`` field. If an email address
   is provided for the username, it extracts only the username portion of the
   string. Additionally, the username is converted to lowercase for
   consistency.

Additional forms
----------------

.. class:: WarnForm

   This form is used when warning the user that an authentication attempt is
   taking place. It contains no visible form fields, but contains two hidden
   fields, ``service`` and ``gateway``. This allows the value of these
   parameters to be passed through the warning process.
