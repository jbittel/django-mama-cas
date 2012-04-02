"""
A management command which deletes invalid tickets from the
database. A ticket is invalidated either when it expires a
configurable number of minutes after creation or by being
consumed. Either situation means the ticket is no longer
valid for future authentication attempts and can be safely
deleted.

These tickets are not removed at the moment of invalidation so
as to provide a historical record in the database of validation
successes and failures. However, this command should be run on
a regular basis to prevent invalid tickets from creating
storage or performance problems.

This command calls ``delete_invalid_tickets()`` for each applicable
model, which determines the tickets that have been invalidated and
deletes them.
"""

from django.core.management.base import NoArgsCommand

from mama_cas.models import LoginTicket
from mama_cas.models import TicketGrantingTicket


class Command(NoArgsCommand):
    help = "Delete expired or consumed CAS tickets from the database"

    def handle_noargs(self, **options):
        # Note that service tickets are not deleted directly,
        # as the delete cascades when their related ticket
        # granting ticket is deleted.
        LoginTicket.objects.delete_invalid_tickets()
        TicketGrantingTicket.objects.delete_invalid_tickets()
