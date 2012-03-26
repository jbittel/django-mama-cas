from django import forms

from mama_cas.models import LoginTicket


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
#    lt = forms.CharField(widget=forms.HiddenInput, initial=LoginTicket.objects.create_login_ticket())
#    lt = forms.CharField(initial=LoginTicket.objects.create_login_ticket())
    lt = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['lt'].initial = LoginTicket.objects.create_login_ticket()

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

        self.data['lt'] = LoginTicket.objects.create_login_ticket()

        return lt
