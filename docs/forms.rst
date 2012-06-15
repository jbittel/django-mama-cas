.. _forms:
.. module:: mama_cas.forms

Authentication forms
====================

django-mama-cas includes form classes for implementing standard username and
password authentication. In most cases, this will be the form of
authentication required. CAS can be used with trust authentication, but the
form that would take is highly implementation dependent. These classes should
suffice for the most common needs.

.. class:: LoginForm

   This is the base form for handling user authentication. It contains the
   following fields:

   ``username``
      The username of the client requesting authentication. The provided string
      is automatically converted to lowercase for consistency. This field is
      required.

    ``password``
       The password of the client requesting authentication. This field is
       required.

    ``service``
       The service that the client is attempting authentication to access,
       typically represented as a URL. This is a hidden, optional field and is
       automatically added to the form when provided.

   The form's ``clean()`` method attempts authentication against the configured
   authentication backends and verifies that the user account is active.
   If either check fails, a ``FormValidation`` error is raised with an
   appropriate error message.

   Note that this form deviates slightly from the official CAS protocol
   specification, as documented in :ref:`protocol-deviations`.

.. class:: LoginFormWarn

   A subclass of :class:`LoginForm` which adds one additional, optional field:

   ``warn``
      A checkbox that indicates whether or not the single sign-on process
      should be transparent. If selected, the user will be prompted before
      being authenticated to another service.

   Although this form is available, the warn parameter has not yet been
   implemented in django-mama-cas |version|.
