.. _templates:

Templates
=========

django-mama-cas comes with a basic, functional template implementing standard
password authentication. It is likely that you will want to either extend the
template with your own customizations or simply replace it entirely.

Included template
-----------------

**mama_cas/login.html**

   This is the main authentication form template used by ``LoginView`` and
   is displayed whenever user credentials are requested. It displays
   appropriate messages or errors to indicate success or failure during the
   login process. When the user logs out, they are redirected back to
   ``LoginView`` so this template is again displayed, along with a message
   indicating they were successfully logged out.

   It is not recommended to edit this template file directly, as changes will
   be overwritten whenever django-mama-cas is updated. Instead use one of the
   two options below.

Extending the template
----------------------

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
   be named ``login.html``, but in this case it makes sense to keep the same
   name of the template being replaced.

   For example, to add an additional header about the form with additional
   styling, create a template with the following content::

      {% extends "mama_cas/login.html" %}
      {% block extra_head %}{{ block.super }}
      <style>#header { font-size:3em; text-align:center; color:#aaa; }</style>
      {% endblock extra_head %}
      {% block header %}
      <h1>If You Can Believe Your Eyes and Ears
      {% endblock header %}

3. Tell django-mama-cas to use the new template. The simplest way is to
   specify it within the URLconf::

      urlpatterns = patterns('',
          url(r'^login/?$',
          LoginView.as_view(template_name="custom_login/login.html"),
          name='cas_login'),
          ...

Replacing the template
----------------------

If the required changes to the login template are substantial, it is easier to
replace the stock template entirely. The process is very similar to the
process of extending the template, as described above. However, instead of
extending the template in step two, replace it entirely.

There are a couple of things you'll likely want to include in a custom
template:

**Messages**
   The ``messages`` framework is used to display information about the user's
   logged in or logged out status. When the message contains HTML, it is
   passed to the template with a ``safe`` tag so the message can be rendered
   appropriately with the HTML intact.

**Non-field errors**
   The ``non_field_errors`` are how the user is informed of authentication
   failures and other login problems.
