import factory

from mama_cas.compat import user_model
from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket
from mama_cas.models import Ticket


class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = user_model
    FACTORY_DJANGO_GET_OR_CREATE = ('username',)

    first_name = 'Ellen'
    last_name = 'Cohen'
    username = first_name.lower()
    email = '%s@example.com' % username
    password = 'mamas&papas'

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class TicketFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Ticket
    ABSTRACT_FACTORY = True

    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        manager = cls._get_manager(target_class)
        return manager.create_ticket(*args, **kwargs)


class ServiceTicketFactory(TicketFactory):
    FACTORY_FOR = ServiceTicket

    service = 'http://www.example.com'


class ProxyGrantingTicketFactory(TicketFactory):
    FACTORY_FOR = ProxyGrantingTicket

    granted_by_st = factory.SubFactory(ServiceTicketFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        return super(ProxyGrantingTicketFactory, cls)._create(target_class,
                'https://www.example.com/', *args, validate=False, **kwargs)


class ProxyTicketFactory(TicketFactory):
    FACTORY_FOR = ProxyTicket

    service = 'http://www.example.com'
    granted_by_pgt = factory.SubFactory(ProxyGrantingTicketFactory)
