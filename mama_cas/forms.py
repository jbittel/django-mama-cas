from string import lower
import logging

from django import forms
from django.utils.http import urlunquote_plus
from django.contrib.auth import authenticate

from mama_cas.models import LoginTicket


logger = logging.getLogger(__name__)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    lt = forms.CharField(widget=forms.HiddenInput)
    service = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        # Don't create a spurious LoginTicket if the form is bound
        if not self.is_bound:
            self.fields['lt'].initial = LoginTicket.objects.create_ticket().ticket

    def clean_username(self):
        """
        Lowercase the username for consistency.
        """
        username = self.cleaned_data.get('username')
        return lower(username)

    def clean_lt(self):
        """
        Verify the provided login ticket. As the validation process will
        consume the login ticket, generate a new login ticket and store
        it in the form.

        If we need to redisplay the form for any reason, this prepares
        for the next authentication attempt. We can modify data because
        we're using a copy of request.POST.
        """
        lt = self.cleaned_data.get('lt')

        if not LoginTicket.objects.validate_ticket(lt):
            raise forms.ValidationError("Invalid login ticket provided")

        self.data['lt'] = LoginTicket.objects.create_ticket().ticket

        return lt

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
            if not authenticate(username=username, password=password):
                logger.warn("Error authenticating user %s" % username)
                raise forms.ValidationError("Could not authenticate user")

        return self.cleaned_data

class LoginFormWarn(LoginForm):
    warn = forms.BooleanField(required=False)
