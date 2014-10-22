import logging

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


class LoginForm(forms.Form):
    """Standard username and password authentication form."""
    username = forms.CharField(label=_("Username"),
                               error_messages={'required':
                                               _("Please enter your username")})
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput,
                               error_messages={'required':
                                               _("Please enter your password")})

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if getattr(settings, 'MAMA_CAS_ALLOW_AUTH_WARN', False):
            self.fields['warn'] = forms.BooleanField(
                    widget=forms.CheckboxInput(),
                    label=_("Warn before automatic login to other services"),
                    required=False)

    def clean(self):
        """
        Pass the provided username and password to the active
        authentication backends and verify the user account is
        not disabled. If authentication succeeds, the ``User`` object
        is assigned to the form so it can be accessed in the view.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                self.user = authenticate(username=username, password=password)
            except Exception:
                logger.exception("Error authenticating %s" % username)
                error_msg = _('Internal error while authenticating user')
                raise forms.ValidationError(error_msg)

            if self.user is None:
                logger.warning("Failed authentication for %s" % username)
                error_msg = _('The username or password is not correct')
                raise forms.ValidationError(error_msg)
            else:
                if not self.user.is_active:
                    logger.warning("User account %s is disabled" % username)
                    error_msg = _('This user account is disabled')
                    raise forms.ValidationError(error_msg)

        return self.cleaned_data


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
        username = self.cleaned_data.get('username').split('@')[0]
        if not username:
            raise forms.ValidationError(_('Invalid username provided'))
        return username
