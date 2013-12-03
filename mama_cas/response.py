try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

try:
    register_namespace = etree.register_namespace
except AttributeError:
    def register_namespace(prefix, uri):
        etree._namespace_map[uri] = prefix

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse


class XmlResponseBase(HttpResponse):
    """
    Base class for XML format CAS service responses.
    """
    prefix = 'cas'
    uri = 'http://www.yale.edu/tp/cas'

    def __init__(self, context=None, content_type=None):
        register_namespace(self.prefix, self.uri)
        content = self.render_xml(context)
        super(XmlResponseBase, self).__init__(content, content_type)

    def ns(self, tag):
        """
        Given an XML tag, output the qualified name for proper
        namespace handling on output.
        """
        return etree.QName(self.uri, tag)


class ValidationResponse(XmlResponseBase):
    """
    Render an XML format CAS service response for a ticket
    validation success or failure.

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
    attribute_formats = ['jasig', 'rubycas', 'namevalue']

    def render_xml(self, context):
        ticket = context.get('ticket')
        error = context.get('error')
        attributes = context.get('attributes')
        pgt = context.get('pgt')
        proxies = context.get('proxies')

        service_response = etree.Element(self.ns('serviceResponse'))
        if ticket:
            auth_success = etree.SubElement(service_response, self.ns('authenticationSuccess'))
            user = etree.SubElement(auth_success, self.ns('user'))
            user.text = ticket.user.username
            if attributes:
                for element in self.get_attribute_elements(attributes):
                    auth_success.append(element)
            if pgt:
                proxy_granting_ticket = etree.SubElement(auth_success, self.ns('proxyGrantingTicket'))
                proxy_granting_ticket.text = pgt.ticket
            if proxies:
                proxy_list = etree.SubElement(auth_success, self.ns('proxies'))
                for p in proxies:
                    proxy = etree.SubElement(proxy_list, self.ns('proxy'))
                    proxy.text = p
        elif error:
            auth_failure = etree.SubElement(service_response, self.ns('authenticationFailure'))
            auth_failure.set('code', error.code)
            auth_failure.text = error.msg

        return etree.tostring(service_response)

    def get_attribute_elements(self, attributes):
        """
        Call the approriate method to retrieve CAS attributes
        according to the currently configured format.
        """
        attr_format = getattr(settings, 'MAMA_CAS_ATTRIBUTE_FORMAT', 'jasig')
        if attr_format.lower() not in self.attribute_formats:
            msg = 'MAMA_CAS_ATTRIBUTE_FORMAT must be set to one of: %s'
            raise ImproperlyConfigured(msg % ', '.join(self.attribute_formats))
        return getattr(self, 'get_%s_elements' % attr_format.lower())(attributes)

    def get_jasig_elements(self, attributes):
        """
        Returns custom CAS attributes in the 'jasig' format:

        <cas:attributes>
            <cas:Name>Value</cas:Name>
        </cas:attributes>
        """
        element = etree.Element(self.ns('attributes'))
        for name, value in attributes:
            attr = etree.SubElement(element, self.ns(name))
            attr.text = value
        return [element]

    def get_rubycas_elements(self, attributes):
        """
        Returns custom CAS attributes in the 'rubycas' format:

        <cas:Name>Value</cas:Name>
        """
        elements = []
        for name, value in attributes:
            element = etree.Element(self.ns(name))
            element.text = value
            elements.append(element)
        return elements

    def get_namevalue_elements(self, attributes):
        """
        Returns custom CAS attributes in the 'namevalue' format:

        <cas:attribute name="Name" value="Value" />
        """
        elements = []
        for name, value in attributes:
            element = etree.Element(self.ns('attribute'))
            element.set('name', name)
            element.set('value', value)
            elements.append(element)
        return elements


class ProxyResponse(XmlResponseBase):
    """
    Render an XML format CAS service response for a proxy request
    success or failure.

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
    def render_xml(self, context):
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
            proxy_failure.text = error.msg

        return etree.tostring(service_response)
