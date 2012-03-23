"""
URLconf for CAS server URIs as described in the CAS protocol.
"""


from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.views.decorators.cache import never_cache

from mama_cas.views import login
from mama_cas.views import logout
from mama_cas.views import validate
from mama_cas.views import service_validate
from mama_cas.views import proxy_validate
from mama_cas.views import proxy


urlpatterns = patterns('',
    url(r'^cas/login/$',
        never_cache(login),
        name='cas_login'),
    url(r'^cas/logout/$',
        never_cache(logout),
        name='cas_logout'),
    url(r'^cas/validate/$',
        never_cache(validate),
        name='cas_validate'),
    url(r'^cas/serviceValidate/$',
        never_cache(service_validate),
        name='cas_service_validate'),
    url(r'^cas/proxyValidate/$',
        never_cache(proxy_validate),
        name='cas_proxy_validate'),
    url(r'^cas/proxy/$',
        never_cache(proxy),
        name='cas_proxy'),
)
