from django.urls import re_path, include

from mama_cas.tests.views import CustomInternalLoginRedirectView

urlpatterns = [
    re_path("", include("mama_cas.urls")),
    re_path(
        "custom_internal_login_redirect/",
        CustomInternalLoginRedirectView.as_view(),
        name="custom_internal_login_redirect",
    ),
]
