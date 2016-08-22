.. _management-commands:

Management Commands
===================

MamaCAS includes custom management commands to aid in some common tasks.
You can see which management commands are available by running::

    $ manage.py

The commands specific to MamaCAS will show up underneath the ``[mama_cas]``
heading. To run a given command::

    $ manage.py <command name>

Commands
--------

**checkservice <service> [<pgtUrl>]**

   Checks the validity and configuration of a given service identifier and
   optional pgtUrl. For example::

      $ manage.py checkservice https://www.example.org
      Invalid Service: https://www.example.org

      $ manage.py checkservice https://www.example.com
      Valid Service: https://www.example.com
      Proxy Allowed: False
      Logout Allowed: False
      Logout URL: None
      Callbacks: ['mama_cas.callbacks.user_name_attributes']

      $ manage.py checkservice https://www.example.com https://proxy.example.com
      Valid Service: https://www.example.com
      Proxy Allowed: True
      Proxy Callback Allowed: True
      Logout Allowed: False
      Logout URL: None
      Callbacks: ['mama_cas.callbacks.user_name_attributes']

**cleanupcas**

   Tickets created by MamaCAS are not removed from the database at the
   moment of invalidation. Running this command will delete all invalid
   tickets from the database. Tickets are invalidated either when they expire
   a configurable number of seconds after creation or by being consumed.
   Either situation means the ticket is no longer valid for future
   authentication attempts and can be safely deleted.

   It is recommended that this command be run on a regular basis so invalid
   tickets do not become a performance or storage concern.
