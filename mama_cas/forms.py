from string import lower
import logging

from django import forms
from django.utils.http import urlunquote_plus
from django.contrib import auth


LOG = logging.getLogger('mama_cas')


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=30)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
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
                    raise forms.ValidationError("This user account is disabled")
            else:
                LOG.warn("Error authenticating user %s" % username)
                raise forms.ValidationError("The username and/or password you provided are not correct")

        return self.cleaned_data

class LoginFormWarn(LoginForm):
    warn = forms.BooleanField(required=False)
