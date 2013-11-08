import logging

from django import forms
from django.contrib.auth import authenticate
from django.utils.http import urlunquote_plus
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


class LoginForm(forms.Form):
    """
    Form implementing standard username and password authentication.
    """
    username = forms.CharField(label=_("Username"),
                               error_messages={'required':
                                               _("Please enter your username")})
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput,
                               error_messages={'required':
                                               _("Please enter your password")})
    service = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_service(self):
        """
        Remove any HTML percent encoding in the service URL.
        """
        service = self.cleaned_data.get('service')
        return urlunquote_plus(service)

    def clean(self):
        """
        Pass the provided username and password to the active
        authentication backends and verify the user account is
        not disabled.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                user = authenticate(username=username, password=password)
            except Exception as e:
                logger.exception("Error authenticating %s" % username)
                error_msg = _("Internal error while authenticating user")
                raise forms.ValidationError(error_msg)

            if user:
                if user.is_active:
                    self.user = user
                else:
                    logger.warning("User account %s is disabled" % username)
                    error_msg = _("This user account is disabled")
                    raise forms.ValidationError(error_msg)
            else:
                logger.warning("Incorrect credentials for %s" % username)
                error_msg = _("The username or password is not correct")
                raise forms.ValidationError(error_msg)
        return self.cleaned_data


class LoginFormWarn(LoginForm):
    """
    Subclass of ``LoginForm`` adding an optional checkbox allowing the
    user to be notified whenever authentication occurs.
    """
    warn = forms.BooleanField(widget=forms.CheckboxInput(),
                              label=_("Warn before automatic login to "
                                      "additional services"),
                              required=False)


class LoginFormEmail(LoginForm):
    """
    Subclass of ``LoginForm`` that extracts the username if an email
    address is provided.
    """
    def clean_username(self):
        """
        Remove an '@<domain>' suffix if present and return only
        the username.
        """
        username = self.cleaned_data.get('username')
        return username.split('@')[0]


class WarnForm(forms.Form):
    """
    Form used to interrupt the automatic authentication process by
    informing the user whenever authentication occurs.

    Visibly, the form consists of a submit button, but these hidden
    fields pass this data through the form during the process.
    """
    service = forms.CharField(widget=forms.HiddenInput, required=False)
    gateway = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_service(self):
        """
        Remove any HTML percent encoding in the service URL.
        """
        service = self.cleaned_data.get('service')
        return urlunquote_plus(service)
