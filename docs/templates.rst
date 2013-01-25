.. _templates:

Templates
=========

django-mama-cas comes with generalized templates to provide a functional
starting point. Most likely you will want to either extend the HTML templates
with your own customizations or replace them entirely.

HTML templates
--------------

**mama_cas/login.html**

   This is the main authentication form template used by ``LoginView``
   implementing standard password authentication and is used whenever user
   credentials are required. It displays appropriate messages or errors to
   indicate success or failure during the login process. When the user logs
   out, they are redirected back to this template, with a message indicating
   a successful logout.

**mama_cas/warn.html**

   This template is used by ``LoginView`` when the warn parameter from
   ``LoginFormWarn`` is in effect. This causes the login process to not be
   transparent to the user. When an authentication attempt occurs, this
   template is displayed to provide continue or cancel options for the user.

.. note:: These template files should not be edited directly, as changes will be overwritten when django-mama-cas is updated.

XML templates
-------------

**mama_cas/validate.xml**

   This template is used for CAS 2.0 service and proxy validation responses.
   In general, this file should not need to be modified as changes will likely
   break expected CAS behavior. Within the body of the authentication success
   block is the include for adding custom user attributes. This include path
   can be changed to one of the following three templates implementing the
   conventional attribute formats.

**mama_cas/attributes-jasig.xml**

   Includes custom user attributes in JASIG format::

      <cas:attributes>
          <cas:givenName>Ellen</cas:givenName>
          <cas:sn>Cohen</cas:sn>
          <cas:email>ellen@example.com</cas:email>
      </cas:attributes>

   django-mama-cas defaults to this custom attributes format.

**mama_cas/attributes-rubycas.xml**

   Includes custom user attributes in RubyCAS format::

      <cas:givenName>Ellen</cas:givenName>
      <cas:sn>Cohen</cas:sn>
      <cas:email>ellen@example.com</cas:email>

**mama_cas/attributes-namevalue.xml**

   Includes custom user attributes in Name-Value format::

      <cas:attribute name='givenName' value='Ellen' />
      <cas:attribute name='sn' value='Cohen' />
      <cas:attribute name='email' value='ellen@example.com' />

**mama_cas/proxy.xml**

   Used for CAS 2.0 proxy-granting ticket validation responses. In general,
   this file should not need to be modified as changes will likely break
   expected CAS behavior.

.. note:: These template files should not be edited directly, as changes will be overwritten when django-mama-cas is updated.

Extending templates
-------------------

The default template provides a number of unused blocks to make it easy to
insert content. If only minor changes are required, it might be simplest to
extend what is already provided. Here are the basic steps involved:

1. Create a custom application and add it to INSTALLED_APPS above
   django-mama-cas. It should look something like this::

      INSTALLED_APPS = (
          ...
          'custom_login',
          'mama_cas',
          ...
      )

2. Create a new login template file within the templates directory of your
   custom application. Assuming an application named ``custom_login``, the
   file would be ``custom_login/templates/custom_login/login.html``.  Putting
   the template within an application specific subdirectory within
   ``templates`` helps keep templates distinct. The template does not need to
   be named ``login.html``, but it can be helpful to mirror the name of the
   template being replaced.

   For example, to add a header above the login form with additional styling,
   create a template with the following content::

      {% extends "mama_cas/login.html" %}
      {% block extra_head %}{{ block.super }}
      <style>#header { font-size:3em; text-align:center; color:#aaa; }</style>
      {% endblock extra_head %}
      {% block header %}
      <h1>If You Can Believe Your Eyes and Ears</h1>
      {% endblock header %}

3. Tell django-mama-cas to use the new template by specifying it within the
   URLconf::

      urlpatterns = patterns('',
          url(r'^login/?$',
          LoginView.as_view(template_name="custom_login/login.html"),
          name='cas_login'),
          ...

Replacing templates
-------------------

If the required changes are substantial, it may be easier to replace the stock
template entirely. Instead of extending the template as described in step two,
replace it entirely.

In addition to a standard form display, there are things you'll likely want to
include in a custom login template:

**Messages**
   The ``messages`` framework displays information about the user's logon
   status. When the message contains HTML, it is passed to the template with
   a ``safe`` tag so the message is rendered with the HTML intact.

**Non-field errors**
   The ``non_field_errors`` inform the user of authentication failures and
   other login problems.
