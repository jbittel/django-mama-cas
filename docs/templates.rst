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
   is displayed whenever user credentials are required. It also handles
   displaying appropriate messages or errors to indicate success or failure
   when logging in. When the user logs out, they are redirected back to
   ``LoginView`` so this template is again displayed, along with a message
   indicating they were successfully logged out.

   It is not recommended that you edit this template directly, as the changes
   will be overwritten whenever django-mama-cas is updated.

Extending the template
----------------------

The included template intentionally provides a number of unused blocks that
make it easy to add content to the existing template. If you only need to
make minor changes, it might be simplest to merely extend what is already
provided.

First, create a new login template file within the templates directory of
your custom application. Assuming an application named ``custom``, the file
would be located at ``custom/templates/custom/login.html``. Putting the
template within an application specific subdirectory within ``templates``
helps to keep templates from multiple applications separated. The template
does not need to be named ``login.html``, but in this case it makes sense
to keep the same name of the template being replaced.

For example, if you wanted to add a custom header to the page with some
additional styling, create a template like this::

   {% extends "mama_cas/login.html" %}
   {% block extra_head %}{{ block.super }}
   <style>#header { font-size:3em; text-align:center; color:#aaa; }</style>
   {% endblock extra_head %}
   {% block header %}<h1>Custom Template</h1>{% endblock header %}

Next, add your custom application to INSTALLED_APPS above django-mama-cas. It
should look something like this::

   INSTALLED_APPS = (
    ...
    'custom',
    'mama_cas',
    ...
   )

Finally, tell django-mama-cas to use your custom login template. The easiest
way is to pass it as a parameter within the URLconf::

   urlpatterns = patterns('',
       url(r'^login/?$',
       LoginView.as_view(template_name="custom/login.html"),
       name='cas_login'),
       ...

Your "Custom Title" heading should now appear on the login page.

Replacing the template
----------------------

If the required changes to the login template would require a substantial
alteration, it is likely simpler to replace the stock template entirely. The
process is very similar to the process of extending the template, as described
above.

There are two areas worth noting about the stock template that ought to be
included or addressed in any custom template that is created:

**Messages**
   The ``messages`` framework is used to display information about the user's
   logged in or logged out status. When the message contains HTML, it is
   passed to the template with a ``safe`` tag so the message can be rendered
   appropriately and the HTML is not stripped.

**Non-field errors**
   The ``non_field_errors`` on the form must be displayed as that is how the
   user is informed of authentication failures and other login problems.
