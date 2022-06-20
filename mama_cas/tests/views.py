from django.views import View
from django.http import HttpResponse


class CustomInternalLoginRedirectView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("CustomInternalLoginRedirectView response")