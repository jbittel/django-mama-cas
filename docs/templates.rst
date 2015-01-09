.. _templates:

Templates
=========

MamaCAS contains templates implementing standard username and password
authentication. Depending on your needs, you can use them as-is, override
portions of them or replace them entirely.

**mama_cas/login.html**

   This template displays the authentication form whenever ``LoginView``
   requires user credentials, as well as authentication success or failure
   information. When the user logs out, they are redirected to this template
   with a logout success message if ``MAMA_CAS_FOLLOW_LOGOUT_URL`` is
   ``False`` or no URL is provided.

**mama_cas/warn.html**

   This template is used by ``LoginView`` when ``MAMA_CAS_ALLOW_AUTH_WARN``
   is enabled and the user has elected to be notified when authentication
   occurs. It provides options for the user to continue the authentication
   process or cancel and log out.

Modifying
---------

To override or extend blocks in the stock templates, first make sure the
custom templates come first in the search order. If the custom templates
exist in a directory specified by ``TEMPLATE_DIRS``, then
``TEMPLATE_LOADERS`` should look something like this::

   TEMPLATE_LOADERS = (
       'django.template.loaders.filesystem.Loader',
       'django.template.loaders.app_directories.Loader',
   )

The base level stock templates are wrappers to simplify extending the stock
templates without circular template inheritance issues. The base template
``mama_cas/login.html`` has a corresponding ``mama_cas/__login.html`` and
``mama_cas/warn.html`` has a corresponding ``mama_cas/__warn.html``.

For example, to add a header above the login form with some additional styling
create a file named ``mama_cas/login.html`` in one of the ``TEMPLATE_DIRS``
that extends ``mama_cas/__login.html``::

   {% extends "mama_cas/__login.html" %}

   {% block styles %}
       {{ block.super }}
       <style>.login-title { color: #aaa; font-size: 2em; }</style>
   {% endblock styles %}

   {% block content_title %}
       If You Can Believe Your Eyes and Ears
   {% endblock content_title %}

Replacing
---------

If the required changes are substantial, then replace the stock templates
entirely. Following the example above, remove the top line that extends
the stock template and include the remainder of the page contents. In addition
to the login form, some elements custom templates should include are:

**Messages**
   The ``messages`` framework displays information to the user for a login,
   logout or authentication notification event.

**Non-field errors**
   The login form's ``non_field_errors`` inform the user of authentication
   failures and other login problems.
