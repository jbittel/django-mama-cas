.. _templates:

Templates
=========

MamaCAS contains templates implementing standard username and password
authentication. Depending on your needs, you can use them as-is, modify
them or replace them entirely.

.. note::

   Changes made directly to the included template files will be lost when
   MamaCAS is updated.

**mama_cas/login.html**

   This template displays the authentication form whenever ``LoginView``
   requires user credentials. It also provides authentication success or
   failure information. When the user logs out, by default they are redirected
   to this template with a logout success message.

**mama_cas/warn.html**

   This template is used by ``LoginView`` when ``MAMA_CAS_ALLOW_AUTH_WARN``
   is enabled and the user has elected to be notified when authentication
   occurs. It provides options for the user to continue the authentication
   process or cancel and log out.

Modifying
---------

To modify or replace the stock templates, first make sure the replacement
templates come first in the search order. If the replacement templates exist
in a directory specified by ``TEMPLATE_DIRS``, then ``TEMPLATE_LOADERS``
should look something like this::

   TEMPLATE_LOADERS = (
       'django.template.loaders.filesystem.Loader',
       'django.template.loaders.app_directories.Loader',
   )

The base level stock templates are wrappers to simplify extending the stock
templates without circular template inheritance issues. The base template
``mama_cas/login.html`` has a corresponding ``mama_cas/__login.html`` and
``mama_cas/warn.html`` has a corresponding ``mama_cas/__warn.html``. Using
this structure, to add a header above the login form with additional styling
create a file named ``mama_cas/login.html`` in one of the ``TEMPLATE_DIRS``
that extends ``mama_cas/__login.html``::

   {% extends "mama_cas/__login.html" %}

   {% block styles %}
       {{ block.super }}
       <style>#header { font-size:3em; text-align:center; color:#aaa; }</style>
   {% endblock styles %}

   {% block header %}
       <h1>If You Can Believe Your Eyes and Ears</h1>
   {% endblock header %}

The stock templates have a variety of blocks defined to make modifications
straightforward. Look through the templates to see what blocks are available.

Replacing
---------

If the required changes are substantial, then replace the stock templates
entirely. Following the example above, simply remove the top line that extends
the stock template. In addition to the login form, some elements custom
templates should include are:

**Messages**
   The ``messages`` framework displays information to the user for a login,
   logout or authentication notification event.

**Non-field errors**
   The login form's ``non_field_errors`` inform the user of authentication
   failures and other login problems.
