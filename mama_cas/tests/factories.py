from datetime import timedelta

from django.contrib.auth.models import User
from django.utils.timezone import now

import factory

from mama_cas.models import ProxyGrantingTicket
from mama_cas.models import ProxyTicket
from mama_cas.models import ServiceTicket
from mama_cas.models import Ticket


class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = User
    FACTORY_DJANGO_GET_OR_CREATE = ('username',)

    first_name = 'Ellen'
    last_name = 'Cohen'
    username = factory.LazyAttribute(lambda o: o.first_name.lower())
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)
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


class InactiveUserFactory(UserFactory):
    first_name = 'Denny'
    last_name = 'Doherty'
    is_active = False


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


class ExpiredServiceTicketFactory(ServiceTicketFactory):
    expires = now() - timedelta(seconds=1)


class ConsumedServiceTicketFactory(ServiceTicketFactory):
    consumed = now() + timedelta(seconds=30)


class ProxyGrantingTicketFactory(TicketFactory):
    FACTORY_FOR = ProxyGrantingTicket

    granted_by_st = factory.SubFactory(ServiceTicketFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if not args:
            args = ('https://www.example.com',)
            kwargs['validate'] = False
        return super(ProxyGrantingTicketFactory, cls)._create(target_class,
                                                              *args, **kwargs)


class ExpiredProxyGrantingTicketFactory(ProxyGrantingTicketFactory):
    expires = now() - timedelta(seconds=1)


class ConsumedProxyGrantingTicketFactory(ProxyGrantingTicketFactory):
    consumed = now()


class ProxyTicketFactory(TicketFactory):
    FACTORY_FOR = ProxyTicket

    service = 'http://www.example.com'
    granted_by_pgt = factory.SubFactory(ProxyGrantingTicketFactory)


class ExpiredProxyTicketFactory(ProxyTicketFactory):
    expires = now() - timedelta(seconds=1)


class ConsumedProxyTicketFactory(ProxyTicketFactory):
    consumed = now()
