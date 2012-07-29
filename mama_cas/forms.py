from string import lower
import logging

from django import forms
from django.utils.http import urlunquote_plus
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _


LOG = logging.getLogger('mama_cas')


class LoginForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=30)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    service = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        """
        Lowercase the username for consistency.
        """
        # TODO check for email addresses
        username = self.cleaned_data.get('username')
        return lower(username)

    def clean_service(self):
        """
        Remove any HTML percent encoding in the service URL.
        """
        service = self.cleaned_data.get('service')
        return urlunquote_plus(service)

    def clean(self):
        """
        Pass the provided username and password to the currently
        configured authentication backends.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = auth.authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    self.user = user
                else:
                    LOG.warn("User account '%s' is disabled" % username)
                    raise forms.ValidationError(_("This user account is disabled"))
            else:
                LOG.warn("Error authenticating user %s" % username)
                raise forms.ValidationError(_("The username and/or password you provided are not correct"))
        return self.cleaned_data

class LoginFormWarn(LoginForm):
    warn = forms.BooleanField(widget=forms.CheckboxInput(),
                              label=_("Prompt me before being authenticated to another service"),
                              required=False)

class LoginFormEmail(LoginForm):
    """
    Subclass of ``LoginForm`` that extracts only the username if an email
    address is provided.
    """
    def clean_username(self):
        """
        If an email address is provided, remove the '@<domain>' portion
        and return only the lowercase username.
        """
        username = self.cleaned_data.get('username').split('@')[0]
        return lower(username)
