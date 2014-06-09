from django.http import HttpResponse

from .compat import etree
from .compat import get_username
from .compat import register_namespace


class CasResponseBase(HttpResponse):
    """
    Base class for CAS 2.0 XML format responses.
    """
    prefix = 'cas'
    uri = 'http://www.yale.edu/tp/cas'

    def __init__(self, context, **kwargs):
        register_namespace(self.prefix, self.uri)
        content = self.render_content(context)
        super(CasResponseBase, self).__init__(content, **kwargs)

    def ns(self, tag):
        """
        Given an XML tag, output the qualified name for proper
        namespace handling on output.
        """
        return etree.QName(self.uri, tag)


class ValidationResponse(CasResponseBase):
    """
    (2.6.2) Render an XML format CAS service response for a
    ticket validation success or failure.

    On validation success:

    <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:authenticationSuccess>
            <cas:user>username</cas:user>
            <cas:proxyGrantingTicket>PGTIOU-84678-8a9d...</cas:proxyGrantingTicket>
            <cas:proxies>
                <cas:proxy>https://proxy2/pgtUrl</cas:proxy>
                <cas:proxy>https://proxy1/pgtUrl</cas:proxy>
            </cas:proxies>
        </cas:authenticationSuccess>
    </cas:serviceResponse>

    On validation failure:

    <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:authenticationFailure code="INVALID_TICKET">
            ticket PT-1856376-1HMgO86Z2ZKeByc5XdYD not recognized
        </cas:authenticationFailure>
    </cas:serviceResponse>
    """
    def render_content(self, context):
        ticket = context.get('ticket')
        error = context.get('error')
        attributes = context.get('attributes')
        pgt = context.get('pgt')
        proxies = context.get('proxies')

        service_response = etree.Element(self.ns('serviceResponse'))
        if ticket:
            auth_success = etree.SubElement(service_response, self.ns('authenticationSuccess'))
            user = etree.SubElement(auth_success, self.ns('user'))
            user.text = get_username(ticket.user)
            if attributes:
                attribute_set = etree.SubElement(auth_success, self.ns('attributes'))
                for name, value in attributes.items():
                    attr = etree.SubElement(attribute_set, self.ns(name))
                    attr.text = value
            if pgt:
                proxy_granting_ticket = etree.SubElement(auth_success, self.ns('proxyGrantingTicket'))
                proxy_granting_ticket.text = pgt.iou
            if proxies:
                proxy_list = etree.SubElement(auth_success, self.ns('proxies'))
                for p in proxies:
                    proxy = etree.SubElement(proxy_list, self.ns('proxy'))
                    proxy.text = p
        elif error:
            auth_failure = etree.SubElement(service_response, self.ns('authenticationFailure'))
            auth_failure.set('code', error.code)
            auth_failure.text = str(error)

        return etree.tostring(service_response, encoding='UTF-8')


class ProxyResponse(CasResponseBase):
    """
    (2.7.2) Render an XML format CAS service response for a proxy
    request success or failure.

    On request success:

    <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:proxySuccess>
            <cas:proxyTicket>PT-1856392-b98xZrQN4p90ASrw96c8</cas:proxyTicket>
        </cas:proxySuccess>
    </cas:serviceResponse>

    On request failure:

    <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
        <cas:proxyFailure code="INVALID_REQUEST">
            'pgt' and 'targetService' parameters are both required
        </cas:proxyFailure>
    </cas:serviceResponse>
    """
    def render_content(self, context):
        ticket = context.get('ticket')
        error = context.get('error')

        service_response = etree.Element(self.ns('serviceResponse'))
        if ticket:
            proxy_success = etree.SubElement(service_response, self.ns('proxySuccess'))
            proxy_ticket = etree.SubElement(proxy_success, self.ns('proxyTicket'))
            proxy_ticket.text = ticket.ticket
        elif error:
            proxy_failure = etree.SubElement(service_response, self.ns('proxyFailure'))
            proxy_failure.set('code', error.code)
            proxy_failure.text = str(error)

        return etree.tostring(service_response, encoding='UTF-8')
