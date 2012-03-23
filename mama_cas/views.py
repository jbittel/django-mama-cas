from django.http import HttpResponse


# 2.1 and 2.2
def login(request,
        template_name='mama_cas/login.html',
        success_url=None, extra_content=None):
    """
    Credential requestor and acceptor.

    This URI operates in two modes: a credential requestor when a GET request
    is received, and a credential acceptor for POST requests.

    As a credential requestor, it takes up to three optional parameters:

    1. service - the identifier of the application the client is accessing. In
       most cases this will be a URL.
    2. renew - if set, a client must present credentials regardless of any
       existing single sign-on session. If set, its value should be ``true``.
    3. gateway - if set, the client will not be prompted for credentials. If
       set, its value should be ``true``.

    The ``renew`` and ``gateway`` parameters are mutually exclusive; if both
    are present, ``renew`` should take precedence.

    """
    service = request.GET.get('service', None)
    renew = request.GET.get('renew', None)
    gateway = request.GET.get('gateway', None)

    if renew and gateway:
        gateway = None

    return render(request, template_name,
                  kwargs,
                  context_instance=context)

# 2.3
def logout(request,
        template_name='mama_cas/logout.html',
        success_url=None, extra_content=None):
    """
    Destroy a client's single sign-on CAS session.
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)

# 2.4
def validate(request):
    """
    Check the validity of a service ticket. [CAS 1.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)

# 2.5
def service_validate(request):
    """
    Check the validity of a service ticket. [CAS 2.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)

# 2.6
def proxy_validate(request):
    """
    Check the validity of a service ticket and additionally
    validate proxy tickets. [CAS 2.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)

# 2.7
def proxy(request):
    """
    Provide proxy tickets to services that have acquired proxy-
    granting tickets. [CAS 2.0]
    """
    return HttpResponse(content='Not Implemented', content_type='text/plain', status=501)
