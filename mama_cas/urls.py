"""
URLconf for CAS server URIs as described in the CAS protocol.
"""

from django.conf.urls import patterns
from django.conf.urls import url
from django.views.decorators.cache import never_cache

from mama_cas.views import login
from mama_cas.views import logout
from mama_cas.views import validate
from mama_cas.views import service_validate
from mama_cas.views import proxy_validate
from mama_cas.views import proxy


urlpatterns = patterns('',
    url(r'^login/$',
        never_cache(login),
        {'template_name': 'mama_cas/login.html'},
        name='cas_login'),
    url(r'^logout/$',
        never_cache(logout),
        {'template_name': 'mama_cas/logout.html'},
        name='cas_logout'),
    url(r'^validate/$',
        never_cache(validate),
        name='cas_validate'),
    url(r'^serviceValidate/$',
        never_cache(service_validate),
        name='cas_service_validate'),
    url(r'^proxyValidate/$',
        never_cache(proxy_validate),
        name='cas_proxy_validate'),
    url(r'^proxy/$',
        never_cache(proxy),
        name='cas_proxy'),
)
