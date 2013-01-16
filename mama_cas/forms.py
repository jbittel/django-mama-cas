from string import lower
import logging

from django import forms
from django.utils.http import urlunquote_plus
from django.contrib import auth
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


class LoginForm(forms.Form):
    """
    Form implementing standard username and password authentication.

    The ``clean()`` method passes the provided username and password to the
    active authentication backend(s) and verifies the user account is not
    disabled.
    """
    username = forms.CharField(label=_("Username"),
                               error_messages={'required': _("Please enter your username")})
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput,
                               error_messages={'required': _("Please enter your password")})
    service = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        """
        Lowercase the username for consistency.
        """
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
                    logger.warn("User account '%s' is disabled" % username)
                    raise forms.ValidationError(_("This user account is disabled"))
            else:
                logger.warn("Error authenticating user %s" % username)
                raise forms.ValidationError(_("The username or password is not correct"))
        return self.cleaned_data


class LoginFormWarn(LoginForm):
    """
    Subclass of ``LoginForm`` adding an optional checkbox allowing the user to
    be notified whenever authentication occurs.
    """
    warn = forms.BooleanField(widget=forms.CheckboxInput(),
                              label=_("Warn before automatic login to additional services"),
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


class WarnForm(forms.Form):
    """
    Form implementing warning for interrupting the automatic authentication
    process.

    Primarily the form consists of a submit button, but these hidden fields
    allow this data to be passed through the form during the process.
    """
    service = forms.CharField(widget=forms.HiddenInput, required=False)
    gateway = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_service(self):
        """
        Remove any HTML percent encoding in the service URL.
        """
        service = self.cleaned_data.get('service')
        return urlunquote_plus(service)
