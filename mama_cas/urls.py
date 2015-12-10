"""
(2) CAS server URIs as described in the CAS protocol.
"""

from django.conf.urls import url

from mama_cas.views import LoginView
from mama_cas.views import LogoutView
from mama_cas.views import ValidateView
from mama_cas.views import ServiceValidateView
from mama_cas.views import ProxyValidateView
from mama_cas.views import ProxyView
from mama_cas.views import WarnView
from mama_cas.views import SamlValidateView


urlpatterns = [
    url(r'^login/?$', LoginView.as_view(), name='cas_login'),
    url(r'^logout/?$', LogoutView.as_view(), name='cas_logout'),
    url(r'^validate/?$', ValidateView.as_view(), name='cas_validate'),
    url(r'^serviceValidate/?$', ServiceValidateView.as_view(), name='cas_service_validate'),
    url(r'^proxyValidate/?$', ProxyValidateView.as_view(), name='cas_proxy_validate'),
    url(r'^proxy/?$', ProxyView.as_view(), name='cas_proxy'),
    url(r'^p3/serviceValidate/?$', ServiceValidateView.as_view(), name='cas_p3_service_validate'),
    url(r'^p3/proxyValidate/?$', ProxyValidateView.as_view(), name='cas_p3_proxy_validate'),
    url(r'^warn/?$', WarnView.as_view(), name='cas_warn'),
    url(r'^samlValidate/?$', SamlValidateView.as_view(), name='cas_saml_validate'),
]
