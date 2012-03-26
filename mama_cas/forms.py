from django import forms

from mama_cas.models import LoginTicket


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    login_ticket = forms.CharField(widget=forms.HiddenInput, initial=LoginTicket.objects.create_login_ticket())
