.. _templates:

Templates
=========

MamaCAS includes templates implementing standard username and password
authentication. Depending on your needs, you can use them as-is, customize
portions or replace them entirely.

**mama_cas/login.html**

   Displays the authentication form whenever ``LoginView`` requires user
   credentials, as well as authentication success or failure information.
   When the user logs out, they are redirected to this template with a logout
   success message if ``MAMA_CAS_FOLLOW_LOGOUT_URL`` is ``False`` or no URL is
   provided.

**mama_cas/warn.html**

   Used by ``LoginView`` when ``MAMA_CAS_ALLOW_AUTH_WARN`` is enabled and the
   user has elected to be notified when authentication occurs. It provides
   options for the user to continue the authentication process or cancel and
   log out.

Modifying
---------

To override or extend blocks in the stock templates, include custom templates
in the search order by specifying the location with the ``DIRS`` option to the
``TEMPLATES`` setting.

The base level stock templates are wrappers to simplify extending the stock
templates without circular template inheritance issues. The base template
``mama_cas/login.html`` has a corresponding ``mama_cas/__login.html`` and
``mama_cas/warn.html`` has a corresponding ``mama_cas/__warn.html``.

For example, to add a header above the login form with some additional styling
create a file named ``mama_cas/login.html`` that extends
``mama_cas/__login.html``::

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
   The ``messages`` framework displays information for login, logout or
   authentication events.

**Non-field errors**
   The login form's ``non_field_errors`` display information regarding
   authentication failures and other login problems.
