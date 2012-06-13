"""
URLconf for CAS server URIs as described in the CAS protocol.
"""

from django.conf.urls import patterns
from django.conf.urls import url

from mama_cas.views import LoginView
from mama_cas.views import LogoutView
from mama_cas.views import ValidateView

from mama_cas.views import service_validate
from mama_cas.views import proxy_validate
from mama_cas.views import proxy


urlpatterns = patterns('',
    url(r'^login/?$',
        LoginView.as_view(),
        name='cas_login'),
    url(r'^logout/?$',
        LogoutView.as_view(),
        name='cas_logout'),
    url(r'^validate/?$',
        ValidateView.as_view(),
        name='cas_validate'),
    url(r'^serviceValidate/?$',
        service_validate,
        name='cas_service_validate'),
    url(r'^proxyValidate/?$',
        proxy_validate,
        name='cas_proxy_validate'),
    url(r'^proxy/?$',
        proxy,
        name='cas_proxy'),
)
