from django import forms
from django.utils.http import urlunquote

from mama_cas.models import LoginTicket


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    lt = forms.CharField(widget=forms.HiddenInput)
    service = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['lt'].initial = LoginTicket.objects.create_ticket()

    def clean_lt(self):
        """
        Verify the specified login ticket exists and check
        that it is not consumed.
        """
        lt = self.cleaned_data.get('lt', None)

        if not lt:
            raise forms.ValidationError("No login ticket provided")

        try:
            login_ticket = LoginTicket.objects.get(ticket=lt)
        except LoginTicket.DoesNotExist:
            raise forms.ValidationError("Invalid login ticket provided")
        else:
            if login_ticket.is_consumed():
                raise forms.ValidationError("Consumed login ticket provided")
            if login_ticket.is_expired():
                raise forms.ValidationError("Expired login ticket provided")

        """
        Whether or not the authentication is successful, consume the
        ``LoginTicket`` so it cannot be used again.
        """
        login_ticket.consume()
        login_ticket.save()

        """
        Generate a new login ticket and store it in the form. If we need
        to redisplay the form for any reason, this prepares for the next
        authentication attempt. We can modify data because we're using a
        copy of request.POST.
        """
        self.data['lt'] = LoginTicket.objects.create_ticket()

        return lt

    def clean_service(self):
        service = self.cleaned_data.get('service')
        return urlunquote(service)

    def clean(self):
        # TODO authenticate username/password
        return self.cleaned_data
