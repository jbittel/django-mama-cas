.. _templates:

Templates
=========

django-mama-cas comes with a very basic template intended to demonstrate how
the authentication pieces function. It is intentionally generic to serve as
a starting point for your own template, or simply replace it wholesale.

Required templates
------------------

**mama_cas/login.html**

   This is the main authentication form template used by ``LoginView``. On
   logout, the user will be redirected to this same template by default once
   the user is logged out.
